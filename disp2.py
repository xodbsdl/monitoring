#!/usr/bin/env python3
"""
🚀 정밀 타이밍 UDP 송신기 (disp_precise.py)
기존 time.sleep(1) 방식의 타이밍 문제를 완전히 해결

주요 개선사항:
- 절대 시간 기준 정밀 타이밍
- 누적 지연 완전 제거  
- 1ms 단위 정확도
- 네트워크 오류 복구
- 실시간 성능 모니터링
"""

import socket
import time
import threading
import os
import signal
import sys
import json
from datetime import datetime

class PrecisionUDPSender:
    def __init__(self):
        # 네트워크 설정
        self.target_ip = "192.168.0.11"  # 수신기(moni) IP
        self.target_port = 12345         # 데이터 전송 포트
        self.control_port = 50001        # 제어 신호 수신 포트
        
        # 타이밍 설정
        self.send_interval = 1.0         # 1초 간격
        self.start_time = None
        self.cycle_count = 0
        
        # 상태 관리
        self.is_running = False
        self.is_sending = False
        
        # 소켓
        self.send_sock = None
        self.control_sock = None
        
        # 성능 통계
        self.stats = {
            'packets_sent': 0,
            'timing_errors': [],
            'network_errors': 0,
            'max_error': 0.0,
            'avg_error': 0.0
        }
        
        # 시뮬레이션 데이터
        self.simulation_states = ["IDLE", "STARTUP", "MAIN_FUELING", "SHUTDOWN"]
        self.current_state_index = 0
        
    def setup_sockets(self):
        """소켓 초기화 및 최적화"""
        try:
            # 📤 데이터 송신용 소켓
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # 🚀 송신 소켓 최적화
            self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 64KB 송신 버퍼
            self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # 포트 재사용
            
            # TOS 설정 (최소 지연)
            try:
                self.send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)
                print("✅ UDP 송신 소켓 TOS 최적화")
            except Exception:
                pass  # Windows에서 지원하지 않을 수 있음
            
            # 📥 제어 신호 수신용 소켓  
            self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.control_sock.bind(("0.0.0.0", self.control_port))
            self.control_sock.settimeout(0.1)  # 100ms 타임아웃
            
            print(f"🚀 소켓 초기화 완료:")
            print(f"   📤 송신: {self.target_ip}:{self.target_port}")
            print(f"   📥 제어: 0.0.0.0:{self.control_port}")
            
        except Exception as e:
            print(f"❌ 소켓 초기화 실패: {e}")
            return False
            
        return True
    
    def generate_simulation_data(self):
        """시뮬레이션 데이터 생성"""
        current_state = self.simulation_states[self.current_state_index]
        
        # 상태별 데이터 생성
        if current_state == "IDLE":
            data = {
                "STATE": "IDLE",
                "카테고리": "H2",
                "압력카테고리": "H70",  
                "SW버전": "v2.1.0",
                "유지보수": "정상",
                "외기온도": f"{20 + (self.cycle_count % 10)}",
                "인렛압력": f"{45.2 + (self.cycle_count % 5)}",
                "출력압력": f"{0.1 + (self.cycle_count % 2)}",
                "SOC": f"{75 + (self.cycle_count % 10)}",
                "유량": f"{0.0}"
            }
        elif current_state == "STARTUP":
            data = {
                "STATE": "STARTUP", 
                "통신모드": "AUTO",
                "초기압력": f"{5.2 + (self.cycle_count % 3)}",
                "APRR": f"{2.1}",
                "타겟압력": f"{70.0}",
                "MP": f"{15.2 + (self.cycle_count % 4)}",
                "MT": f"{-5 + (self.cycle_count % 8)}",
                "TV": "OPEN",
                "퓨얼링압력": f"{25.4 + (self.cycle_count % 6)}",
                "SOC": f"{76 + (self.cycle_count % 8)}",
                "유량": f"{12.5 + (self.cycle_count % 5)}"
            }
        elif current_state == "MAIN_FUELING":
            data = {
                "STATE": "MAIN_FUELING",
                "설정출력압력": f"{70.0}",
                "MP": f"{65.8 + (self.cycle_count % 3)}",
                "MT": f"{15 + (self.cycle_count % 10)}",
                "TV": "MODULATE",
                "퓨얼링압력": f"{68.2 + (self.cycle_count % 4)}",
                "SOC": f"{80 + (self.cycle_count % 15)}",
                "유량": f"{45.2 + (self.cycle_count % 8)}"
            }
        else:  # SHUTDOWN
            data = {
                "STATE": "SHUTDOWN",
                "MP": f"{5.1 + (self.cycle_count % 2)}",
                "MT": f"{25 + (self.cycle_count % 5)}",
                "TV": "CLOSE",
                "퓨얼링압력": f"{2.1 + (self.cycle_count % 3)}",
                "출력수소온도": f"{30 + (self.cycle_count % 8)}",
                "충전시간": f"{int((self.cycle_count % 300) / 60)}분{(self.cycle_count % 300) % 60}초",
                "최종충전량": f"{15.8 + (self.cycle_count % 5)}",
                "최종충전금액": f"{25400 + (self.cycle_count % 1000)}",
                "SOC": f"{95 + (self.cycle_count % 5)}",
                "유량": f"{0.0}"
            }
        
        return data
    
    def format_udp_packet(self, data):
        """UDP 패킷 포맷 생성 (moni.py 호환)"""
        state = data["STATE"]
        fields = []
        
        for key, value in data.items():
            if key != "STATE":
                fields.append(f"{key}:{value}")
        
        packet = f"{state}|{','.join(fields)}"
        return packet.encode('utf-8')
    
    def precision_sleep(self, target_time):
        """🎯 정밀한 대기 함수 (1ms 정확도)"""
        while True:
            current_time = time.perf_counter()
            if current_time >= target_time:
                break
                
            remaining = target_time - current_time
            
            if remaining > 0.002:  # 2ms 이상 남으면 sleep 사용
                time.sleep(remaining * 0.9)  # 90%만 sleep
            # 마지막 2ms는 busy-wait으로 정밀 대기
    
    def send_data_loop(self):
        """🚀 정밀 타이밍 데이터 송신 루프"""
        print("🚀 정밀 타이밍 데이터 송신 시작")
        
        # 절대 시간 기준 시작점
        self.start_time = time.perf_counter()
        self.cycle_count = 0
        
        # 성능 측정 변수
        last_stats_time = time.time()
        timing_errors = []
        
        while self.is_sending:
            try:
                # 📅 다음 송신 시간 계산 (절대 시간 기준)
                target_send_time = self.start_time + (self.cycle_count * self.send_interval)
                
                # 🎯 정밀한 시간까지 대기
                self.precision_sleep(target_send_time)
                
                # 📊 실제 송신 시간 측정
                actual_send_time = time.perf_counter()
                timing_error = actual_send_time - target_send_time
                
                # 📤 데이터 생성 및 전송
                sim_data = self.generate_simulation_data()
                packet = self.format_udp_packet(sim_data)
                
                self.send_sock.sendto(packet, (self.target_ip, self.target_port))
                
                # 📊 성능 통계 업데이트
                self.stats['packets_sent'] += 1
                timing_errors.append(abs(timing_error))
                
                if abs(timing_error) > self.stats['max_error']:
                    self.stats['max_error'] = abs(timing_error)
                
                # 🔄 상태 순환 (10초마다)
                if self.cycle_count > 0 and self.cycle_count % 10 == 0:
                    self.current_state_index = (self.current_state_index + 1) % len(self.simulation_states)
                    print(f"🔄 상태 변경: {self.simulation_states[self.current_state_index]}")
                
                # 📊 5초마다 성능 리포트
                current_time = time.time()
                if current_time - last_stats_time >= 5.0:
                    if timing_errors:
                        avg_error = sum(timing_errors) / len(timing_errors)
                        max_recent = max(timing_errors)
                        
                        print(f"📊 성능 리포트: {self.stats['packets_sent']}패킷 송신")
                        print(f"   ⏱️  평균 타이밍 오차: {avg_error*1000:.1f}ms")
                        print(f"   🎯 최대 타이밍 오차: {max_recent*1000:.1f}ms") 
                        print(f"   🌐 네트워크 오류: {self.stats['network_errors']}회")
                        
                        # 성능 경고
                        if avg_error > 0.01:  # 10ms 이상
                            print(f"   ⚠️ 타이밍 정확도 주의 필요")
                        elif avg_error < 0.002:  # 2ms 이하
                            print(f"   ✅ 타이밍 정확도 우수")
                        
                        timing_errors.clear()
                    
                    last_stats_time = current_time
                
                self.cycle_count += 1
                
            except socket.error as e:
                self.stats['network_errors'] += 1
                print(f"🌐 네트워크 오류 #{self.stats['network_errors']}: {e}")
                
                if self.stats['network_errors'] > 10:
                    print("🔄 소켓 재초기화 시도")
                    self.setup_sockets()
                    self.stats['network_errors'] = 0
                    
            except Exception as e:
                print(f"❌ 송신 오류: {e}")
                break
        
        print(f"🔚 데이터 송신 종료 - 총 {self.stats['packets_sent']}패킷 송신")
    
    def control_listener(self):
        """📥 제어 신호 수신 스레드"""
        print("📥 제어 신호 대기 중...")
        
        while self.is_running:
            try:
                data, addr = self.control_sock.recvfrom(1024)
                command = data.decode().strip().upper()
                
                print(f"📨 제어 신호 수신: '{command}' from {addr}")
                
                if command == "ON":
                    if not self.is_sending:
                        self.is_sending = True
                        # 송신 스레드 시작
                        send_thread = threading.Thread(target=self.send_data_loop, daemon=True)
                        send_thread.start()
                        print("🟢 데이터 송신 시작")
                    else:
                        print("⚠️ 이미 송신 중입니다")
                        
                elif command == "OFF":
                    if self.is_sending:
                        self.is_sending = False
                        print("🔴 데이터 송신 중지")
                    else:
                        print("⚠️ 송신이 활성화되지 않았습니다")
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"📥 제어 신호 수신 오류: {e}")
    
    def print_final_stats(self):
        """📊 최종 성능 통계"""
        print("\n" + "="*50)
        print("📊 최종 성능 통계")
        print("="*50)
        print(f"총 송신 패킷: {self.stats['packets_sent']}")
        print(f"최대 타이밍 오차: {self.stats['max_error']*1000:.1f}ms")
        print(f"네트워크 오류: {self.stats['network_errors']}회")
        
        if self.stats['packets_sent'] > 0:
            success_rate = ((self.stats['packets_sent'] - self.stats['network_errors']) / self.stats['packets_sent']) * 100
            print(f"송신 성공률: {success_rate:.1f}%")
        
        total_time = time.perf_counter() - self.start_time if self.start_time else 0
        if total_time > 0:
            print(f"총 실행 시간: {total_time:.1f}초")
            print(f"평균 송신율: {self.stats['packets_sent']/total_time:.1f} 패킷/초")
    
    def run(self):
        """🚀 메인 실행 함수"""
        print("🚀 정밀 타이밍 UDP 송신기 시작")
        print(f"🎯 타겟: {self.target_ip}:{self.target_port}")
        print(f"⏱️  송신 간격: {self.send_interval}초")
        print("="*50)
        
        # 소켓 초기화
        if not self.setup_sockets():
            return
        
        self.is_running = True
        
        # 제어 신호 수신 스레드 시작
        control_thread = threading.Thread(target=self.control_listener, daemon=True)
        control_thread.start()
        
        try:
            print("🎮 제어 명령 대기 중... (Ctrl+C로 종료)")
            print("💡 moni.py에서 ON 버튼을 눌러주세요")
            
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의한 종료")
        except Exception as e:
            print(f"❌ 실행 오류: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """🧹 정리 작업"""
        print("🧹 시스템 정리 중...")
        
        self.is_running = False
        self.is_sending = False
        
        if self.send_sock:
            self.send_sock.close()
        if self.control_sock:
            self.control_sock.close()
            
        self.print_final_stats()
        print("✅ 정리 완료")

if __name__ == "__main__":
    sender = PrecisionUDPSender()
    sender.run()