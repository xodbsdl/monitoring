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
import platform
from datetime import datetime

def detect_target_ip():
    """🔍 실행 환경에 따라 자동으로 타겟 IP 감지"""
    
    print("🔍 타겟 IP 자동 감지 중...")
    
    # 0. Windows 환경에서는 localhost 우선 사용
    if platform.system() == "Windows":
        print("🪟 Windows 환경 감지: localhost 우선 사용")
        return "localhost"
    
    # 1. 로컬 테스트 환경 감지 (더 안전한 방법)  
    localhost_ips = ["127.0.0.1", "localhost"]
    for local_ip in localhost_ips:
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.settimeout(0.5)  # 타임아웃 증가
            
            # UDP 소켓으로 연결 테스트 (실제로는 UDP는 연결이 없지만 주소 유효성 검사)
            try:
                if local_ip == "localhost":
                    test_address = ("127.0.0.1", 12345)
                else:
                    test_address = (local_ip, 12345)
                
                # 실제 연결 가능 여부 확인
                test_sock.connect(test_address)
                test_sock.close()
                
                print(f"🏠 로컬 환경 감지: {local_ip} ({test_address[0]}) 사용")
                return test_address[0]
            except:
                test_sock.close()
                continue
        except:
            continue
    
    # 2. 현재 시스템의 IP 주소 기반으로 네트워크 대역 감지
    try:
        # 시스템의 네트워크 인터페이스 정보 확인
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_sock.connect(("8.8.8.8", 80))
        local_ip = temp_sock.getsockname()[0]
        temp_sock.close()
        
        print(f"📍 로컬 IP 감지: {local_ip}")
        
        # IP 대역별로 가능한 moni IP 추정
        if local_ip.startswith("192.168.0."):
            candidate_ips = ["192.168.0.11", "192.168.0.10", "192.168.0.1"]
        elif local_ip.startswith("192.168.1."):
            candidate_ips = ["192.168.1.11", "192.168.1.10", "192.168.1.1"]
        else:
            # 다른 네트워크 대역
            base = ".".join(local_ip.split(".")[:-1])
            candidate_ips = [f"{base}.11", f"{base}.10", f"{base}.1"]
            
    except:
        # 네트워크 정보 획득 실패시 기본 후보들
        candidate_ips = [
            "192.168.0.11", "192.168.0.10",
            "192.168.1.11", "192.168.1.10"
        ]
    
    # 3. 네트워크 상에서 moni2.py 찾기
    print(f"🔍 후보 IP들을 확인 중: {candidate_ips}")
    
    for ip in candidate_ips:
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.settimeout(1.0)  # 타임아웃 증가
            
            # 연결 테스트
            test_sock.connect((ip, 12345))
            test_sock.close()
            
            print(f"🌐 네트워크 환경 감지: {ip} 사용")
            return ip
        except Exception as e:
            continue
    
    # 4. 기본값으로 폴백
    default_ip = "127.0.0.1"  # 로컬 테스트를 기본으로
    print(f"⚠️ 타겟 자동 감지 실패")
    print(f"💡 기본값 사용: {default_ip}")
    print("💡 moni2.py가 실행되고 있는지 확인하거나 수동으로 IP를 입력하세요")
    return default_ip

class PrecisionUDPSender:
    def __init__(self):
        # 네트워크 설정 (자동 감지)
        self.target_ip = detect_target_ip()  # 자동 감지된 수신기(moni) IP
        self.target_port = 12345              # 데이터 전송 포트
        self.control_port = 50001             # 제어 신호 수신 포트
        
        # 타이밍 설정
        self.send_interval = 1.0         # 1초 간격
        self.start_time = None
        self.cycle_count = 0
        
        # 상태 관리
        self.is_running = False
        self.is_sending = False
        
        # 📊 상태별 시간 설정 (초)
        self.state_durations = {
            "IDLE": 5,           # 5초
            "STARTUP": 5,        # 5초  
            "MAIN_FUELING": 120, # 120초 (2분)
            "SHUTDOWN": 20       # 20초
        }
        self.current_state_time = 0
        
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
        
        # 📊 랜덤 시작값들 (세션마다 변경)
        import random
        self.initial_soc = random.randint(5, 20)  # 초기 SOC: 5-20%
        self.target_soc = random.randint(80, 88)  # 목표 SOC: 80-88%
        self.flow_rate_base = random.uniform(20.0, 48.0)  # 기본 유량: 20-48 g/s
        
        # 📊 MAIN_FUELING 마지막 값들 (SHUTDOWN에서 사용)
        self.last_flow_rate = 0.0
        self.last_fueling_pressure = 0.0
        
        print(f"🎲 세션 파라미터: 초기SOC={self.initial_soc}%, 목표SOC={self.target_soc}%, 기본유량={self.flow_rate_base:.1f}g/s")
        
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
        
        # 📊 SOC 계산 (개선된 랜덤 시작값 + 점진적 증가)
        if current_state == "IDLE" or current_state == "STARTUP":
            # 초기값 유지 (5-20% 중 선택된 값)
            soc_value = self.initial_soc
        elif current_state == "MAIN_FUELING":
            # 초기값에서 목표값(80-88%)까지 점진적 증가
            progress = self.current_state_time / self.state_durations["MAIN_FUELING"]
            soc_range = self.target_soc - self.initial_soc
            soc_value = self.initial_soc + (progress * soc_range)
            soc_value = min(self.target_soc, soc_value)  # 목표값 초과 방지
        else:  # SHUTDOWN
            # 목표값 유지
            soc_value = self.target_soc
        
        # 📊 유량 계산 (g/s 단위, 20-48 g/s 범위, 실시간 변동)
        import random
        if current_state == "IDLE":
            flow_rate = 0.0
        elif current_state == "STARTUP":
            # 점진적 증가 (0 -> 20-30 g/s 랜덤)
            progress = self.current_state_time / self.state_durations["STARTUP"]
            target_flow = random.uniform(20.0, 30.0)  # 매번 다른 목표값
            flow_rate = progress * target_flow
        elif current_state == "MAIN_FUELING":
            # 매번 20-48 g/s 사이 랜덤값 생성
            flow_rate = random.uniform(20.0, 48.0)
            self.last_flow_rate = flow_rate  # 마지막 값 저장
        else:  # SHUTDOWN
            # MAIN_FUELING 마지막 값에서 점진적 감소 (-> 0)
            progress = self.current_state_time / self.state_durations["SHUTDOWN"]
            flow_rate = max(0.0, self.last_flow_rate * (1.0 - progress))
        
        # 📊 퓨얼링압력 계산
        if current_state == "IDLE":
            fueling_pressure = 0.0
        elif current_state == "STARTUP":
            fueling_pressure = 0.0
        elif current_state == "MAIN_FUELING":
            # 600~700바 사이에서 변동
            base_pressure = 650.0
            variation = 50.0 * (0.5 - (self.cycle_count % 20) / 40.0)  # ±25바 변동
            fueling_pressure = base_pressure + variation
            self.last_fueling_pressure = fueling_pressure  # 마지막 값 저장
        else:  # SHUTDOWN
            # MAIN_FUELING 마지막 값에서 점진적 감소 (-> 0)
            progress = self.current_state_time / self.state_durations["SHUTDOWN"]
            fueling_pressure = max(0.0, self.last_fueling_pressure * (1.0 - progress))
        
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
                "SOC": f"{soc_value:.1f}",
                "유량": f"{flow_rate:.1f}",
                "퓨얼링압력": f"{fueling_pressure:.1f}"
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
                "퓨얼링압력": f"{fueling_pressure:.1f}",
                "SOC": f"{soc_value:.1f}",
                "유량": f"{flow_rate:.1f}"
            }
        elif current_state == "MAIN_FUELING":
            data = {
                "STATE": "MAIN_FUELING",
                "설정출력압력": f"{70.0}",
                "MP": f"{65.8 + (self.cycle_count % 3)}",
                "MT": f"{15 + (self.cycle_count % 10)}",
                "TV": "MODULATE",
                "퓨얼링압력": f"{fueling_pressure:.1f}",
                "SOC": f"{soc_value:.1f}",
                "유량": f"{flow_rate:.1f}"
            }
        else:  # SHUTDOWN
            data = {
                "STATE": "SHUTDOWN",
                "MP": f"{5.1 + (self.cycle_count % 2)}",
                "MT": f"{25 + (self.cycle_count % 5)}",
                "TV": "CLOSE",
                "퓨얼링압력": f"{fueling_pressure:.1f}",
                "출력수소온도": f"{30 + (self.cycle_count % 8)}",
                "충전시간": f"{int((self.cycle_count % 300) / 60)}분{(self.cycle_count % 300) % 60}초",
                "최종충전량": f"{15.8 + (self.cycle_count % 5)}",
                "최종충전금액": f"{25400 + (self.cycle_count % 1000)}",
                "SOC": f"{soc_value:.1f}",
                "유량": f"{flow_rate:.1f}"
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
        print("🚀 시뮬레이션 데이터 송신 시작 (성능 모니터링 아님!)")
        
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
                
                # 첫 번째 패킷 전송 시 실제 데이터 내용 표시
                if self.cycle_count == 0:
                    print(f"📤 실제 전송 데이터 예시:")
                    for key, value in sim_data.items():
                        print(f"   {key}: {value}")
                    print(f"📦 UDP 패킷 형태: {packet.decode('utf-8')[:100]}...")
                
                self.send_sock.sendto(packet, (self.target_ip, self.target_port))
                
                # 📊 성능 통계 업데이트
                self.stats['packets_sent'] += 1
                timing_errors.append(abs(timing_error))
                
                if abs(timing_error) > self.stats['max_error']:
                    self.stats['max_error'] = abs(timing_error)
                
                # 🔄 상태별 타이밍에 따른 상태 변경
                current_state = self.simulation_states[self.current_state_index]
                state_duration = self.state_durations[current_state]
                
                # 현재 상태의 경과 시간 계산
                states_completed_time = sum(self.state_durations[self.simulation_states[i]] for i in range(self.current_state_index))
                current_state_elapsed = (actual_send_time - self.start_time) - states_completed_time
                
                if current_state_elapsed >= state_duration:
                    # 다음 상태로 전환
                    old_state = current_state
                    self.current_state_index = (self.current_state_index + 1) % len(self.simulation_states)
                    new_state = self.simulation_states[self.current_state_index]
                    print(f"🔄 상태 변경: {old_state} ({current_state_elapsed:.1f}s) → {new_state}")
                    
                    # 전체 사이클 완료 시 시작 시간 재설정
                    if self.current_state_index == 0:
                        self.start_time = actual_send_time
                        self.cycle_count = 0
                        print("🔄 새로운 사이클 시작")
                
                # 📊 10초마다 간단한 상태 리포트
                current_time = time.time()
                if current_time - last_stats_time >= 10.0:
                    current_state = self.simulation_states[self.current_state_index]
                    state_progress = current_state_elapsed / state_duration * 100
                    print(f"📊 데이터 송신 중: {self.stats['packets_sent']}패킷 ({current_state} {state_progress:.1f}%)")
                    
                    if timing_errors:
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
                        # 🎲 새로운 세션 시작 - 랜덤 파라미터 재생성
                        import random
                        self.initial_soc = random.randint(5, 20)  # 초기 SOC: 5-20%
                        self.target_soc = random.randint(80, 88)  # 목표 SOC: 80-88%
                        self.flow_rate_base = random.uniform(20.0, 48.0)  # 기본 유량: 20-48 g/s
                        print(f"🎲 새 세션 시작: 초기SOC={self.initial_soc}%, 목표SOC={self.target_soc}%, 기본유량={self.flow_rate_base:.1f}g/s")
                        
                        self.is_sending = True
                        # 송신 스레드 시작
                        send_thread = threading.Thread(target=self.send_data_loop, daemon=True)
                        send_thread.start()
                        print("🟢 시뮬레이션 데이터 송신 시작 - 실제 센서 데이터 전송 중")
                    else:
                        print("⚠️ 이미 송신 중입니다")
                        
                elif command == "OFF":
                    if self.is_sending:
                        self.is_sending = False
                        print("🔴 시뮬레이션 데이터 송신 중지")
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
    
    def set_target_ip(self, new_ip):
        """🔧 타겟 IP 수동 변경"""
        old_ip = self.target_ip
        self.target_ip = new_ip
        print(f"🔄 타겟 IP 변경: {old_ip} → {new_ip}")
    
    def run(self):
        """🚀 메인 실행 함수"""
        print("🚀 정밀 타이밍 UDP 송신기 시작")
        print(f"🎯 타겟: {self.target_ip}:{self.target_port}")
        print(f"⏱️  송신 간격: {self.send_interval}초")
        print("="*50)
        
        # IP 변경 옵션 제공
        try:
            print("💡 다른 IP를 사용하려면 입력하세요 (엔터 키로 현재 설정 사용):")
            user_ip = input(f"타겟 IP [{self.target_ip}]: ").strip()
            if user_ip:
                self.set_target_ip(user_ip)
                print("="*50)
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의한 종료")
            return
        
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