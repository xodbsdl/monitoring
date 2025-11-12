

import socket
import threading
import time
import csv
import os
import signal
import atexit
import sys
import matplotlib
import platform

# PyInstaller 빌드를 위한 안전한 matplotlib 백엔드 설정
def setup_matplotlib_backend():
    """PyInstaller 빌드 환경에 안전한 matplotlib 백엔드 설정"""
    system = platform.system()
    
    # PyInstaller 실행 환경 감지
    is_frozen = getattr(sys, 'frozen', False)
    
    if is_frozen:
        # PyInstaller로 빌드된 exe 환경 - PIL 충돌 방지
        print("exe 빌드 환경 감지: Agg 백엔드 강제 사용 (PIL 충돌 방지)")
        try:
            matplotlib.use('Agg', force=True)
            return 'Agg'
        except Exception as e:
            print(f"Agg 백엔드 설정 실패: {e}")
            # 최후의 수단으로 TkAgg 시도
            try:
                matplotlib.use('TkAgg', force=True)
                return 'TkAgg'
            except Exception:
                matplotlib.use('Agg', force=True)
                return 'Agg'
    
    if system == "Linux":
        # 디스플레이 환경 확인
        display = os.environ.get('DISPLAY', '')
        
        if not display:
            # headless 환경 (SSH 등)
            matplotlib.use('Agg')
            print(" headless 환경 감지: Agg 백엔드 사용 (파일 저장만 가능)")
            return 'Agg'
        else:
            # GUI 환경 - 안전한 백엔드 순서로 시도 (PyInstaller 호환)
            backend_options = ['TkAgg', 'Qt5Agg', 'Agg']  # TkAgg를 첫 번째로
            for backend in backend_options:
                try:
                    # 백엔드별 안전한 테스트 (PyInstaller 호환)
                    if backend == 'TkAgg':
                        # tkinter 안전 테스트 (PyInstaller용)
                        try:
                            import tkinter
                            matplotlib.use('TkAgg', force=True)
                            print(f" GUI 환경: {backend} 백엔드 사용 (안전 모드)")
                            return backend
                        except Exception:
                            continue
                    elif backend == 'Qt5Agg':
                        try:
                            import PyQt5
                            matplotlib.use('Qt5Agg', force=True)
                            print(f" GUI 환경: {backend} 백엔드 사용")
                            return backend
                        except ImportError:
                            continue
                    else:  # Agg
                        matplotlib.use('Agg', force=True)
                        print(" Fallback: Agg 백엔드 사용")
                        return backend
                        
                except Exception as e:
                    print(f" {backend} 백엔드 실패: {e}")
                    continue
            
            # 모든 GUI 백엔드 실패 시
            matplotlib.use('Agg', force=True)
            print(" 모든 GUI 백엔드 실패: Agg 백엔드로 폴백")
            return 'Agg'
    else:
        # Windows/macOS - PyInstaller 빌드 고려
        try:
            matplotlib.use('TkAgg', force=True)
            print(f" {system} 환경: TkAgg 백엔드 사용 (빌드 호환)")
            return 'TkAgg'
        except Exception:
            print(f" {system} 환경: 기본 백엔드 사용")
            return matplotlib.get_backend()

# 백엔드 초기화
current_backend = setup_matplotlib_backend()

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm

# PyInstaller 빌드를 위한 안전한 한글 폰트 설정
def setup_korean_font():
    """PyInstaller 빌드 환경에 안전한 한글 폰트 설정"""
    try:
        # PyInstaller 실행 환경 감지
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            # exe 빌드 환경에서는 시스템 기본 폰트 사용
            print("exe 빌드 환경: 시스템 기본 폰트 사용")
            plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            return 'Malgun Gothic'
        
        # 일반 환경에서의 폰트 설정
        import matplotlib.font_manager as fm
        
        # 사용 가능한 한글 폰트 찾기 (안전하게)
        try:
            available_fonts = [f.name for f in fm.fontManager.ttflist]
        except Exception:
            # 폰트 매니저 실패 시 기본 폰트 사용
            available_fonts = []
        
        korean_fonts = []
        
        # 우선순위별 한글 폰트 리스트 (라즈베리파이 최적화)
        if platform.system() == "Linux":
            # 라즈베리파이/Linux용 폰트 우선순위
            preferred_fonts = [
                'NanumGothic', 'Nanum Gothic', 'NanumBarunGothic',
                'Noto Sans CJK KR', 'Noto Sans KR', 
                'DejaVu Sans', 'Liberation Sans', 'sans-serif'
            ]
        else:
            # Windows/macOS용 폰트 우선순위
            preferred_fonts = [
                'Malgun Gothic', 'NanumGothic', 'Nanum Gothic',
                'Apple Gothic', 'DejaVu Sans', 'Liberation Sans'
            ]
        
        # 사용 가능한 한글 폰트 찾기
        for font in preferred_fonts:
            if font in available_fonts:
                korean_fonts.append(font)
        
        if korean_fonts:
            plt.rcParams['font.family'] = korean_fonts
            plt.rcParams['axes.unicode_minus'] = False
            print(f"한글 폰트 설정 완료: {korean_fonts[0]}")
            return korean_fonts[0]
        else:
            # 폰트가 없으면 기본값 사용
            plt.rcParams['font.family'] = ['sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            print("한글 폰트 없음: 기본 폰트 사용")
            if platform.system() == "Linux":
                print("나눔 폰트 설치: sudo apt install fonts-nanum fonts-noto-cjk")
            return 'sans-serif'
            
    except Exception as e:
        print(f"폰트 설정 오류: {e}")
        # 최후의 안전망
        try:
            plt.rcParams['font.family'] = ['sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass  # 완전 실패 시 무시
        return 'sans-serif'

# 폰트 초기화
setup_korean_font()

def get_optimal_figure_size():
    """화면 크기에 맞는 최적의 figure 크기 계산"""
    try:
        if current_backend == 'Agg':
            # headless 환경에서는 고정 크기 사용
            return (12, 8)
        
        # GUI 환경에서는 화면 크기 감지 시도 (안전하게)
        screen_width = 1024  # 기본값
        screen_height = 600
        
        try:
            # PyInstaller 빌드 환경에서 안전한 화면 크기 감지
            is_frozen = getattr(sys, 'frozen', False)
            
            if is_frozen:
                # exe 환경에서는 기본값 사용 (안전)
                screen_width = 1024
                screen_height = 768
                print("exe 빌드 환경: 기본 화면 크기 사용 (1024x768)")
            elif current_backend == 'Qt5Agg':
                # Qt5를 먼저 시도
                try:
                    from PyQt5 import QtWidgets
                    app = QtWidgets.QApplication.instance()
                    if app is None:
                        app = QtWidgets.QApplication([])
                    screen = app.primaryScreen()
                    if screen:
                        size = screen.size()
                        screen_width = size.width()
                        screen_height = size.height()
                except Exception:
                    screen_width = 1024
                    screen_height = 768
            else:
                # tkinter 시도 (PyInstaller 안전 모드)
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()  # 창 숨기기
                    screen_width = root.winfo_screenwidth()
                    screen_height = root.winfo_screenheight()
                    root.destroy()
                except Exception:
                    screen_width = 1024
                    screen_height = 768
                
        except Exception as e:
            print(f"화면 크기 감지 실패: {e}, 기본값 사용")
            screen_width = 1024
            screen_height = 768
        
        # 라즈베리파이 일반적인 해상도에 맞춤
        if screen_width <= 800:
            return (9, 5)   # 매우 작은 화면 (라즈베리파이 터치스크린)
        elif screen_width <= 1024:
            return (13, 6.5)  # 작은 화면용 - 가로 더 증가: 12 → 13
        elif screen_width <= 1366:
            return (16, 8.5)  # 중간 화면용 - 가로 더 증가: 15 → 16
        else:
            return (22, 11)  # 큰 화면용 - 가로 더 증가: 20 → 22
    except Exception as e:
        print(f"figure 크기 계산 오류: {e}")
        # 라즈베리파이 기본값
        return (10, 6)

def get_font_sizes():
    """화면 크기에 맞는 폰트 크기 반환"""
    screen_size = get_optimal_figure_size()
    base_size = screen_size[0]  # 가로 크기를 기준으로
    
    if base_size <= 10:  # 작은 화면 (라즈베리파이 등)
        return {
            'title': 12,
            'subtitle': 10, 
            'normal': 8,
            'small': 7,
            'tiny': 6
        }
    elif base_size <= 14:  # 중간 화면
        return {
            'title': 15,
            'subtitle': 12,
            'normal': 10,
            'small': 8,
            'tiny': 7
        }
    else:  # 큰 화면
        return {
            'title': 18,
            'subtitle': 15,
            'normal': 12,
            'small': 10,
            'tiny': 8
        }

def check_dependencies():
    """라즈베리파이에서 필요한 패키지 확인 및 설치 안내"""
    missing_packages = []
    
    # 필수 패키지 확인
    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")
    
    try:
        import matplotlib
    except ImportError:
        missing_packages.append("matplotlib")
    
    # 한글 폰트 확인 (Linux 환경에서만)
    if platform.system() == "Linux":
        font_installed = False
        font_paths = [
            '/usr/share/fonts/truetype/nanum/',
            '/usr/share/fonts/truetype/noto/'
        ]
        for path in font_paths:
            if os.path.exists(path):
                font_installed = True
                break
        
        if not font_installed:
            print(" 한글 폰트가 설치되지 않았습니다.")
            print("설치 명령: sudo apt install fonts-nanum fonts-noto-cjk")
    
    if missing_packages:
        print(f"누락된 패키지: {', '.join(missing_packages)}")
        print(f"설치 명령: pip install {' '.join(missing_packages)}")
        return False
    
    print("모든 필수 패키지가 설치되어 있습니다.")
    return True

# 의존성 확인
check_dependencies()

# 폰트 크기 설정
font_sizes = get_font_sizes()
print(f"폰트 크기 설정: 제목={font_sizes['title']}, 일반={font_sizes['normal']}")

def format_time(seconds):
    """초를 분:초 형태로 변환"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

# UDP 수신기 설정 (disp → moni)
UDP_IP = "0.0.0.0"      # 모든 IP에서 수신
UDP_PORT = 12345        # 데이터 수신 포트
DATA_FILE = "monitoring_data.csv"

# 제어신호 송신 설정 (moni → disp)
def detect_disp_ip():
    """실행 환경에 따라 disp.py의 IP 자동 감지"""
    import platform
    
    # Windows 환경에서는 localhost 사용
    if platform.system() == "Windows":
        print("Windows 환경 감지: localhost 사용")
        return "localhost"
    
    # Linux 환경에서는 네트워크 IP 감지
    try:
        import socket
        # 로컬 IP 획득
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        if local_ip.startswith("192.168.0"):
            return "192.168.0.12"
        elif local_ip.startswith("192.168.1"):
            return "192.168.1.12"
        else:
            return "192.168.0.12"
    except:
        return "192.168.0.12"

DISP_IP = detect_disp_ip()  # 자동 감지된 송신기(disp) IP
CONTROL_PORT = 50001        # 제어 신호 포트

print(f"제어 신호 타겟: {DISP_IP}:{CONTROL_PORT}")

udp_thread = None
data_rows = []
lock = threading.Lock()

# 중복 데이터 방지를 위한 변수들
last_received_data = {"content": "", "timestamp": 0}
duplicate_prevention_lock = threading.Lock()

# 상태 순서 검증을 위한 변수
expected_state_sequence = ["IDLE", "STARTUP", "MAIN_FUELING", "SHUTDOWN"]
current_sequence_index = [0]  # 현재 기대하는 상태 인덱스

# ON/OFF 상태
data_on = [False]  # 리스트로 감싸서 클로저에서 변경 가능
current_state = ["대기중"]  # 현재 상태


def udp_receiver():
    global data_rows  # 전역 변수 선언 추가
    
    # UDP 소켓 생성
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 포트 재사용 허용
    
    # 성능 최적화: 소켓 버퍼 크기 증가 (패킷 손실 방지)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # 64KB 수신 버퍼
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 64KB 송신 버퍼
        print("UDP 소켓 버퍼 최적화: 64KB")
    except Exception as e:
        print(f"소켓 버퍼 설정 실패: {e}")
    
    # 블로킹 모드 최적화 (CPU 사용량 감소)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)  # 최소 지연 설정
        print("UDP 소켓 TOS 최적화")
    except Exception:
        pass  # Windows에서 지원하지 않을 수 있음
    
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.05)  # 타임아웃 단축: 0.1초 → 0.05초 (응답성 향상)
    print("UDP 수신기 시작됨 (성능 최적화)")
    
    # 성능 카운터 추가
    packet_count = 0
    error_count = 0
    last_stats_time = time.time()
    
    # 소켓 버퍼 비우기 (이전 데이터 제거)
    try:
        sock.settimeout(0.01)  # 아주 짧은 타임아웃으로
        discarded_count = 0
        while True:
            try:
                old_data, _ = sock.recvfrom(2048)
                discarded_count += 1
                if discarded_count > 100:  # 무한 루프 방지
                    break
            except socket.timeout:
                break
        if discarded_count > 0:
            print(f"이전 UDP 데이터 {discarded_count}개 정리됨")
        sock.settimeout(0.1)  # 원래 타임아웃으로 복원
    except Exception as e:
        print(f"UDP 버퍼 정리 중 오류: {e}")
        sock.settimeout(0.1)
    
    while True:
        if not data_on[0]:
            time.sleep(0.1)
            continue
            
        line = None
        timestamp = time.time()
        
        # UDP에서 데이터 수신
        try:
            packet, addr = sock.recvfrom(4096)  # 버퍼 크기 증가: 2048 → 4096
            line = packet.decode('utf-8', errors='ignore').strip()  # 안전한 디코딩
            current_time = time.time()
            
            # 성능 통계 업데이트
            packet_count += 1
            
            # 1초(1000ms)마다 수신한 패킷 원본 출력 (그래프 업데이트와 동기화)
            if current_time - last_stats_time >= 1.0:
                print(f"{line}")
                last_stats_time = current_time
                
        except socket.timeout:
            # OFF 상태인지 다시 확인
            if not data_on[0]:
                # print("UDP 수신기: OFF 상태 감지, 수신 중단")
                break
            # 타임아웃은 정상 동작이므로 조용히 계속
            continue
            
        except (UnicodeDecodeError, socket.error) as e:
            error_count += 1
            # print(f"UDP 수신 오류 #{error_count}: {e}")
            if error_count > 10:  # 연속 오류 시 소켓 재시작
                # print("UDP 소켓 재시작 필요")
                break
            continue
        except Exception as e:
            error_count += 1
            # print(f"예상치 못한 UDP 오류: {e}")
            continue
        
        if not line:
            time.sleep(0.1)
            continue
        
        # 상태 순서 검증 - 첫 수신 후 순서대로 진행
        if '|' in line:
            temp_state = line.split('|', 1)[0]
            current_index = current_sequence_index[0]
            
            # print(f"상태 검증: 현재인덱스={current_index}({expected_state_sequence[current_index]}), 수신상태={temp_state}")
            
            # 데이터가 없거나 처음 수신하는 경우 - 어떤 상태든 허용
            if len(data_rows) == 0:
                if temp_state in expected_state_sequence:
                    new_index = expected_state_sequence.index(temp_state)
                    current_sequence_index[0] = new_index
                    # print(f"첫 데이터 수신: {temp_state} (인덱스 {new_index})")
                else:
                    pass
                    # print(f"알 수 없는 상태이지만 첫 데이터로 허용: {temp_state}")
            elif temp_state == "IDLE":
                # IDLE은 언제나 허용 (리셋)
                current_sequence_index[0] = 0
                # print(f"IDLE 상태로 리셋: 인덱스 0")
            elif temp_state in expected_state_sequence:
                expected_index = expected_state_sequence.index(temp_state)
                
                # 다음 순서 상태이면 허용
                if expected_index == current_index + 1:
                    current_sequence_index[0] = expected_index
                    # print(f"다음 상태로 진행: {temp_state} (인덱스 {expected_index})")
                # 현재 상태와 같으면 허용 (반복)
                elif expected_index == current_index:
                    pass
                    # print(f"현재 상태 반복: {temp_state}")
                # 그 외는 무시
                else:
                    # print(f"순서 불일치 데이터 무시 (현재인덱스: {current_index}, 수신인덱스: {expected_index}): {line[:50]}...")
                    continue
        
        # 새로운 데이터 형식 파싱: STATE|field1:value1,field2:value2,...
        if '|' in line:
            state_part, data_part = line.split('|', 1)
            current_state[0] = state_part
            
            # 필드:값 쌍들을 파싱
            field_value_pairs = data_part.split(',')
            parsed_data = {'STATE': state_part}
            for pair in field_value_pairs:
                if ':' in pair:
                    field, value = pair.split(':', 1)
                    parsed_data[field.strip()] = value.strip()
        else:
            # 기존 형식 지원 (하위 호환성)
            data_parts = line.split(",")
            parsed_data = {'STATE': data_parts[0] if data_parts else 'UNKNOWN'}
            current_state[0] = parsed_data['STATE']
        
        # 중복 데이터 방지 로직 (더 엄격하게)
        with duplicate_prevention_lock:
            # 동일한 내용의 데이터가 0.2초 이내에 중복 수신되면 완전히 무시
            if (line == last_received_data["content"] and 
                timestamp - last_received_data["timestamp"] < 0.2):
                # print(f"중복 데이터 무시: {line[:50]}...")  # 로그 제거
                continue
            
            # 마지막 수신 데이터 업데이트
            last_received_data["content"] = line
            last_received_data["timestamp"] = timestamp
        
        with lock:
            # 메모리 최적화: 최대 데이터 개수 제한 (메모리 누수 방지)
            MAX_DATA_POINTS = 3600  # 1시간 분량 (1초 간격 기준)
            
            # 파싱된 데이터를 저장
            data_rows.append([timestamp, parsed_data])
            # 마지막 수신 시간 기록 (데이터 누락 감지용)
            udp_receiver.last_data_time = timestamp
            
            # 메모리 관리: 오래된 데이터 자동 정리
            if len(data_rows) > MAX_DATA_POINTS:
                # 앞의 600개(10분) 데이터 제거하여 메모리 절약
                removed_count = len(data_rows) - MAX_DATA_POINTS + 600
                data_rows = data_rows[removed_count:]
                # print(f"메모리 정리: {removed_count}개 오래된 데이터 제거")
            
            # 성능 최적화: 간격 계산 (선택적 로깅)
            if len(data_rows) > 1:
                prev_timestamp = data_rows[-2][0]
                interval = timestamp - prev_timestamp
                if interval > 1.5:  # 1.5초 이상 간격이면 경고
                    pass
                    # print(f"경고: {parsed_data['STATE']} - 긴 간격 감지! 누락의심")
        
        # 메모리 효율적 저장 (실시간 파일 저장 제거)
    
    # 안전한 UDP 수신기 종료
    try:
        if sock:
            sock.shutdown(socket.SHUT_RDWR)  # 소켓 종료 시그널
            sock.close()
        # print("UDP 수신기 정상 종료됨")
    except Exception as e:
        pass
        # print(f"UDP 소켓 종료 오류: {e}")
    finally:
        pass
        # print(f"최종 통계: {packet_count}패킷 처리, {error_count}오류 발생")

# --- 상태별 필드 정의 (SOC, 유량 공통 추가) ---
state_fields = {
    "IDLE": ["카테고리", "압력카테고리", "SW버전", "유지보수", "외기온도", "인렛압력", "출력압력", "SOC", "유량"],
    "STARTUP": ["통신모드", "초기압력", "APRR", "타겟압력", "MP", "MT", "TV", "퓨얼링압력", "SOC", "유량"],
    "MAIN_FUELING": ["설정출력압력", "MP", "MT", "TV", "퓨얼링압력", "SOC", "유량"],
    "SHUTDOWN": ["MP", "MT", "TV", "퓨얼링압력", "출력수소온도", "충전시간", "최종충전량", "최종충전금액", "SOC", "유량"]
}

# --- 그래프 및 상태 패널 레이아웃 ---

plt.ion()
optimal_size = get_optimal_figure_size()
fig = plt.figure(figsize=optimal_size)
print(f"📱 화면 크기 설정: {optimal_size[0]}×{optimal_size[1]} 인치")

# 라즈베리파이 최적화된 레이아웃
gs = gridspec.GridSpec(3, 3, 
                      height_ratios=[0.08, 0.82, 0.10], 
                      width_ratios=[0.9, 0.6, 1.85],
                      hspace=0.08, wspace=0.02)  # wspace 축소: 0.04 → 0.02

# 여백 조정 - 오른쪽 여백 더 증가
fig.subplots_adjust(left=0.02, right=0.94, top=0.95, bottom=0.08)

# 상단: 버튼 영역
ax_btn_area = plt.subplot(gs[0, :])
ax_btn_area.axis('off')

# 중간 왼쪽: 상태 패널
ax_state = plt.subplot(gs[1, 0])
ax_state.axis('off')

# 중간 가운데: 현재 값 패널 (새로 추가)
ax_current = plt.subplot(gs[1, 1])
ax_current.axis('off')

# 중간 오른쪽: 그래프 영역  
ax_graph = plt.subplot(gs[1, 2])

# 하단: 슬라이더 영역
ax_slider_area = plt.subplot(gs[2, 2])
ax_slider_area.axis('off')

# 그래프에 표시할 필드와 해당 색상, 심볼 정의 (확장 가능)
plot_field_config = {
    "SOC": {
        "color": "#2E8B57",      # 진한 초록 (Sea Green)
        "emoji": "",        # 배터리 표시
        "unit": "%"
    },
    "유량": {
        "color": "#FF6347",      # 빨간색 (Tomato) - 그래프와 일치
        "emoji": "",       # 유량 표시
        "unit": "g/s"
    },
    "퓨얼링압력": {
        "color": "#4169E1",      # 파란색 (Royal Blue) - 그래프와 일치
        "emoji": "",      # 압력 표시
        "unit": "bar"
    }
}

fields_to_plot = list(plot_field_config.keys())  # 설정된 필드들만 그래프로 표시
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', '#ff8800', '#00ccff', '#aa00ff']  # fallback 색상
lines = {}

cursor_x = [0]
cursor_line = None
cursor_idx = [0]  # 현재 커서가 가리키는 데이터 인덱스
cursor_active = [False]  # 커서가 활성화되었는지 여부
update_timer = None

slider = None
btn_on = None
btn_off = None

# 그래프 축들을 저장할 전역 변수
all_graph_axes = []  # 모든 그래프 축들 (main + twin axes)

def cleanup_on_exit():
    """프로그램 종료 시 완전한 정리"""
    global data_on, update_timer
    print("시스템 정리 중...")
    
    # 데이터 수신 중지
    data_on[0] = False
    
    # 타이머 중지
    if update_timer is not None:
        try:
            update_timer.stop()
            print("타이머 정지됨")
        except:
            pass
    
    # 신호 파일들 정리
    try:
        # stop 신호 파일 생성 (disp 프로세스 종료용)
        with open("stop_signal.txt", "w") as f:
            f.write("stop")
        print("stop 신호 파일 생성됨")
        
        # 잠시 대기 후 모든 신호 파일 제거
        time.sleep(0.5)
        for signal_file in ["start_signal.txt", "stop_signal.txt", "disp_running.lock", "disp_sim.py"]:
            if os.path.exists(signal_file):
                os.remove(signal_file)
                print(f"{signal_file} 제거됨")
    except Exception as e:
        print(f"신호 파일 정리 오류: {e}")
    
    # UDP 수신기 종료 대기
    global udp_thread
    if udp_thread is not None and udp_thread.is_alive():
        print("UDP 수신기 종료 대기 중...")
        time.sleep(0.5)
    
    print("시스템 정리 완료")

# 종료 시 정리 함수 등록
atexit.register(cleanup_on_exit)

def clear_all_graphs():
    """그래프 화면 완전 초기화"""
    global lines, cursor_line, cursor_idx, cursor_active
    
    try:
        # 모든 그래프 라인 제거
        for field in lines:
            if lines[field]:
                for line in lines[field]:
                    if line:
                        line.remove()
        lines.clear()
        
        # 커서 라인 제거
        if cursor_line:
            cursor_line.remove()
            cursor_line = None
        
        # 커서 상태 초기화
        cursor_idx[0] = 0
        cursor_active[0] = False
        cursor_x[0] = 0
        
        # 그래프 영역 초기화
        if 'ax_graph' in globals():
            ax_graph.clear()
            
        print("그래프 화면 초기화 완료")
        
    except Exception as e:
        print(f"그래프 초기화 오류: {e}")

def get_field_indices():
    # 헤더 없이 데이터만 들어오므로, 각 상태별 필드 인덱스 추정
    # row = [timestamp, state, ...fields...]
    indices = {}
    for state, fields in state_fields.items():
        for i, f in enumerate(fields):
            indices[f] = i + 2  # 0:timestamp, 1:state
    return indices

field_indices = get_field_indices()

def update_state_panel(idx=None):
    ax_state.clear()
    ax_state.axis('off')
    
    # 제목 (동적 폰트 크기)
    ax_state.text(0.5, 0.99, "시스템 상태 모니터링", fontsize=font_sizes['title'], fontweight='bold', 
                 ha='center', va='top', color='darkblue')
    
    # 4가지 상태를 항상 표시 - 각각 고정된 영역 할당
    states = ["IDLE", "STARTUP", "MAIN_FUELING", "SHUTDOWN"]
    state_names_kr = ["대기", "시작", "충전", "종료"]
    colors_state = ['lightblue', 'lightyellow', 'lightgreen', 'lightpink']
    
    # 한글-영문 상태명 매핑
    state_kr_to_en = {
        "대기": "IDLE",
        "시작": "STARTUP", 
        "충전": "MAIN_FUELING",
        "종료": "SHUTDOWN"
    }
    
    current = current_state[0] if not cursor_active[0] else None
    cursor_data = None
    
    with lock:
        if data_rows and cursor_active[0]:
            if idx is None:
                idx = cursor_idx[0] if cursor_idx[0] < len(data_rows) else len(data_rows) - 1
            if idx < len(data_rows):
                row = data_rows[idx]
                if len(row) > 1 and isinstance(row[1], dict):
                    current = row[1].get('STATE', 'UNKNOWN')
                    # 한글 상태명을 영문으로 변환
                    if current in state_kr_to_en:
                        current = state_kr_to_en[current]
                    cursor_data = [row[0], row[1].copy()]  # 복사본 생성
        elif data_rows and not cursor_active[0]:
            # 실시간 모드: 최신 데이터 사용
            row = data_rows[-1]
            if len(row) > 1 and isinstance(row[1], dict):
                current = row[1].get('STATE', 'UNKNOWN')
                # 한글 상태명을 영문으로 변환
                if current in state_kr_to_en:
                    current = state_kr_to_en[current]
                cursor_data = [row[0], row[1].copy()]  # 복사본 생성
    
    # 커서 정보 표시 (커서 활성화시에만) - 깔끔한 박스로 표시
    if cursor_active[0] and cursor_data:
        timestamp = cursor_data[0] - (data_rows[0][0] if data_rows else 0)
        
        # 커서 정보를 하나의 박스에 정리해서 표시
        cursor_info_lines = [f" 시간: {format_time(timestamp)}"]
        
        # 딕셔너리에서 그래프 표시 필드들의 값 수집
        if len(cursor_data) > 1 and isinstance(cursor_data[1], dict):
            data_dict = cursor_data[1]
            for field_name, field_config in plot_field_config.items():
                if field_name in data_dict:
                    marker = field_config["emoji"]
                    unit = field_config.get("unit", "")
                    value = data_dict[field_name]
                    value_text = f"{marker} {field_name}: {value}"
                    if unit:
                        value_text += f" {unit}"
                    cursor_info_lines.append(value_text)
        
        # 하나의 박스에 모든 커서 정보 표시 (동적 폰트 크기)
        cursor_text = "\n".join(cursor_info_lines)
        ax_state.text(0.5, 0.93, cursor_text, fontsize=font_sizes['normal'], 
                     fontweight='bold', color='darkred', ha='center', va='top',
                     bbox=dict(boxstyle="round,pad=0.4", facecolor='lightyellow', 
                              alpha=0.95, edgecolor='red', linewidth=2))
    
    # 실시간 모드일 때 SOC와 유량 표시 (커서 비활성화 시)
    elif not cursor_active[0] and data_rows:
        latest_row = data_rows[-1]
        if len(latest_row) > 1 and isinstance(latest_row[1], dict):
            data_dict = latest_row[1]
            
            # 실시간 정보를 하나의 박스에 정리해서 표시
            live_info_lines = [f"[LIVE] 실시간 데이터"]
            
            # SOC와 유량만 표시
            for field_name, field_config in plot_field_config.items():
                if field_name in data_dict:
                    marker = field_config["emoji"]
                    unit = field_config.get("unit", "")
                    value = data_dict[field_name]
                    value_text = f"{marker} {field_name}: {value}"
                    if unit:
                        value_text += f" {unit}"
                    live_info_lines.append(value_text)
            
            # 실시간 정보 박스 표시 (동적 폰트 크기)
            live_text = "\n".join(live_info_lines)
            ax_state.text(0.5, 0.93, live_text, fontsize=font_sizes['normal'], 
                         fontweight='bold', color='darkgreen', ha='center', va='top',
                         bbox=dict(boxstyle="round,pad=0.4", facecolor='lightgreen', 
                                  alpha=0.95, edgecolor='darkgreen', linewidth=2))
    
    # 4개 상태를 2x2 형태로 배치 - 확장된 크기와 간격
    available_height = 0.75  # 사용 가능한 높이 확장
    box_width = 0.485  # 각 박스 너비 확장 (전체 너비의 48.5%)
    box_height = available_height / 2.3  # 각 박스 높이 확장
    
    # 2x2 격자 위치 정의 - 최적화된 간격
    margin_x = 0.005  # 좌우 여백 최소화
    gap_x = 0.01      # 박스 간 가로 간격
    gap_y = 0.025     # 박스 간 세로 간격 조정
    
    positions = [
        (margin_x, 0.75 - box_height),                                    # 좌상단: IDLE
        (margin_x + box_width + gap_x, 0.75 - box_height),               # 우상단: STARTUP  
        (margin_x, 0.75 - 2*box_height - gap_y),                         # 좌하단: MAIN_FUELING
        (margin_x + box_width + gap_x, 0.75 - 2*box_height - gap_y)      # 우하단: SHUTDOWN
    ]
    
    for i, (state, name_kr) in enumerate(zip(states, state_names_kr)):
        x_start, y_start = positions[i]
        y_end = y_start
        actual_box_height = box_height * 0.9  # 실제 박스 높이 (10% 여백)
        
        is_current = (state == current)
        
        # 상태별 배경 박스 (2x2 형태)
        if is_current:
            # 현재 상태는 진한 색상과 테두리
            ax_state.add_patch(plt.Rectangle((x_start, y_end), box_width, actual_box_height, 
                                           facecolor=colors_state[i], alpha=0.9, 
                                           edgecolor='darkblue', linewidth=3))
        else:
            # 비활성 상태는 연한 색상
            ax_state.add_patch(plt.Rectangle((x_start, y_end), box_width, actual_box_height, 
                                           facecolor='lightgray', alpha=0.5, 
                                           edgecolor='gray', linewidth=1))
        
        # 상태명 표시 (박스 상단 중앙에 배경과 함께)
        title_text = f"[{name_kr}] {state}"
        ax_state.text(x_start + box_width/2, y_start + actual_box_height - 0.005, 
                     title_text, 
                     fontsize=9, fontweight='bold' if is_current else 'normal',
                     color='darkblue' if is_current else 'gray',
                     ha='center', va='top',
                     bbox=dict(boxstyle="round,pad=0.15", 
                              facecolor='white' if is_current else 'lightgray', 
                              alpha=0.95, edgecolor='darkblue' if is_current else 'gray',
                              linewidth=1.5))
        
        # 각 상태의 데이터 표시 (현재 상태 또는 커서 위치의 상태)
        # 커서 활성화 시: 커서 위치의 각 상태별 데이터 표시
        # 실시간 모드 시: 현재 상태만 데이터 표시
        should_show_data = False
        state_data_dict = None
        
        if cursor_active[0] and cursor_data:
            # 커서 모드: 모든 상태에 데이터 표시 가능하도록 준비
            should_show_data = (state == current)  # 현재 커서 위치의 상태만 표시
            if should_show_data and len(cursor_data) > 1 and isinstance(cursor_data[1], dict):
                state_data_dict = cursor_data[1]
        elif is_current and cursor_data:
            # 실시간 모드: 현재 활성 상태만 표시
            should_show_data = True
            if len(cursor_data) > 1 and isinstance(cursor_data[1], dict):
                state_data_dict = cursor_data[1]
        
        if should_show_data and state_data_dict:
            y_detail = y_start + actual_box_height - 0.05  # 상태명 아래부터 시작
            
            # 박스 내에서 표시 가능한 최대 라인 수 계산
            max_lines = min(15, int((actual_box_height - 0.04) / 0.016))  # 더 많은 라인 표시
            
            # 딕셔너리에서 모든 필드 표시 (STATE 제외)
            field_count = 0
            for field, value in state_data_dict.items():
                if field == 'STATE':  # STATE는 이미 표시했으므로 제외
                    continue
                if field_count >= max_lines:  # 박스 크기 내에서만 표시
                    break
                
                # 그래프 표시 필드는 강조 표시
                if field in plot_field_config:
                    field_config = plot_field_config[field]
                    color_text = field_config["color"]
                    weight_text = 'bold'
                    marker = field_config["emoji"]
                    unit = field_config.get("unit", "")
                    display_text = f"{marker} {field}: {value}"
                    if unit:
                        display_text += f" {unit}"
                    font_size = 9.5  # 폰트 크기: 7.5 → 9.5 (+2pt)
                else:
                    color_text = 'black'
                    weight_text = 'normal'
                    display_text = f"{field}: {value}"
                    font_size = 8.5  # 폰트 크기: 6.5 → 8.5 (+2pt)
                
                # 텍스트 길이 제한 (박스에 맞춰 조정)
                if len(display_text) > 28:
                    display_text = display_text[:25] + "..."
                
                # Y 위치 계산 (더 촘촘한 라인 간격)
                text_y = y_detail - (field_count * 0.016)
                if text_y > y_end + 0.01:  # 박스 아래쪽 여백 확보
                    ax_state.text(x_start + 0.01, text_y, display_text, fontsize=font_size, 
                                color=color_text, fontweight=weight_text, 
                                verticalalignment='top')
                    field_count += 1
    
    ax_state.set_xlim(0, 1)
    ax_state.set_ylim(0, 1)
    fig.canvas.draw_idle()

def update_current_values():
    """현재 수신 값 패널 업데이트 (1초마다 최신 데이터 표시)"""
    ax_current.clear()
    ax_current.axis('off')
    ax_current.set_xlim(0, 1)
    ax_current.set_ylim(0, 1)
    
    # 제목
    ax_current.text(0.5, 0.95, "실시간 수신 데이터", fontsize=16, fontweight='bold',  # 14 → 16
                   ha='center', va='top', color='darkgreen')
    
    if not data_rows:
        ax_current.text(0.5, 0.5, "데이터 수신 대기 중...", fontsize=14,  # 12 → 14
                       ha='center', va='center', color='gray')
        return
    
    # 최신 데이터 사용
    latest_row = data_rows[-1]
    if len(latest_row) < 2 or not isinstance(latest_row[1], dict):
        return
    
    data_dict = latest_row[1]
    current_state_name = data_dict.get('STATE', 'UNKNOWN')
    
    # 현재 상태 표시 (상태별 색상 적용)
    state_color_map = {
        "IDLE": "lightblue",
        "STARTUP": "lightyellow",
        "MAIN_FUELING": "lightgreen",
        "SHUTDOWN": "lightpink"
    }
    current_state_color = state_color_map.get(current_state_name, "lightgray")
    
    ax_current.text(0.5, 0.85, f"현재 상태: {current_state_name}", fontsize=14,  # 12 → 14
                   fontweight='bold', ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=current_state_color, alpha=0.8))
    
    # 수신 시간 표시
    current_time = latest_row[0] - (data_rows[0][0] if data_rows else 0)
    ax_current.text(0.5, 0.75, f"수신 시간: {format_time(current_time)}", fontsize=12,  # 10 → 12
                   ha='center', va='center')
    
    # 딕셔너리에서 모든 필드 값들 표시 (STATE 제외)
    y_pos = 0.68  # 시작 위치를 조금 올림
    field_count = 0
    for field, value in data_dict.items():
        if field == 'STATE':  # STATE는 이미 표시했으므로 제외
            continue
        if field_count >= 12:  # 최대 12개 필드 표시
            break
        
        # 그래프 표시 필드는 강조
        if field in plot_field_config:
            field_config = plot_field_config[field]
            color = field_config["color"]
            marker = field_config["emoji"]
            unit = field_config.get("unit", "")
            display_text = f"{marker} {field}: {value}"
            if unit:
                display_text += f" {unit}"
            font_weight = 'bold'
            font_size = 11  # 폰트 크기: 9 → 11 (+2pt)
        else:
            color = 'black'
            display_text = f"{field}: {value}"
            font_weight = 'normal'
            font_size = 10  # 폰트 크기: 8 → 10 (+2pt)
        
        # Y 위치가 패널 아래를 벗어나지 않도록 체크
        if y_pos > 0.05:  # 하단 여백 확보
            ax_current.text(0.03, y_pos, display_text, fontsize=font_size, 
                           color=color, fontweight=font_weight, 
                           verticalalignment='center')
        
        field_count += 1
        y_pos -= 0.055  # 간격을 더 좁게 (0.07에서 0.055로)
    
    fig.canvas.draw_idle()

def update_graph():
    global cursor_line, all_graph_axes
    
    # OFF 상태에서도 데이터가 있으면 그래프 표시 (CSV 로드 후 보기 위해)
    # 단, 실시간 수신 중이 아닐 때만 (커서 모드)
    if not data_on[0] and not cursor_active[0]:
        # OFF 상태이고 커서도 비활성화면 그래프 업데이트 안함
        return
    
    # ON 상태일 때만 축 정리 및 그래프 클리어
    for ax in fig.get_axes():
        if ax != ax_state and ax != ax_btn_area and ax != ax_slider_area:
            if hasattr(ax, '_is_twin_axis'):
                ax.remove()
    
    # 축 리스트 초기화
    all_graph_axes.clear()
    all_graph_axes.append(ax_graph)  # 메인 축 추가
    
    # clear 호출 시 cursor_line도 자동으로 제거되므로 초기화
    cursor_line = None
    ax_graph.clear()
    
    with lock:
        if not data_rows or len(data_rows) < 2:
            ax_graph.text(0.5, 0.5, '[CHART] 데이터 대기 중...', transform=ax_graph.transAxes, 
                         ha='center', va='center', fontsize=16, color='gray')
            ax_graph.set_title(f"실시간 모니터링 - {'ON' if data_on[0] else 'OFF'}", 
                              fontsize=14, fontweight='bold')
            ax_graph.grid(True, linestyle=':', alpha=0.3)
            fig.canvas.draw_idle()
            return
        
        # 모든 데이터 포인트 표시 (누적)
        recent_data = data_rows
        xs = [row[0] - data_rows[0][0] for row in recent_data] if data_rows else []
        
        # 모든 데이터에서 사용 가능한 필드들을 동적으로 수집
        all_fields = set()
        for row in recent_data:
            if len(row) > 1 and isinstance(row[1], dict):
                all_fields.update(row[1].keys())
        
        # plot_field_config에 정의된 필드들 중 실제 데이터에 있는 것만 선택
        # 순서를 명시적으로 지정하여 항상 같은 순서로 표시
        preferred_order = ["SOC", "유량", "퓨얼링압력"]
        graph_fields = [field for field in preferred_order if field in all_fields]
        
        axes_list = []  # Y축 리스트
        plot_count = 0
        
        # 동적으로 발견된 필드들을 그래프로 표시
        for i, field in enumerate(graph_fields):
            ys = []
            for row in recent_data:
                val = None
                if len(row) > 1 and isinstance(row[1], dict):
                    field_value = row[1].get(field)
                    if field_value is not None:
                        try:
                            val = float(field_value)
                        except (ValueError, TypeError):
                            val = None
                ys.append(val)
            
            # None이 아닌 값이 하나라도 있으면 그래프에 추가
            if any(y is not None for y in ys):
                # 첫 번째 필드는 기본 Y축 사용
                if plot_count == 0:
                    current_ax = ax_graph
                else:
                    # 두 번째부터는 새로운 Y축 생성
                    current_ax = ax_graph.twinx()
                    current_ax._is_twin_axis = True  # 표시용
                    all_graph_axes.append(current_ax)  # 클릭 감지용 리스트에 추가
                    # Y축 위치 조정 (간격 더 축소)
                    if plot_count > 1:
                        current_ax.spines['right'].set_position(('outward', 35 * (plot_count - 1)))
                
                # 필드 설정에서 색상, 이모지, 단위 가져오기
                field_config = plot_field_config.get(field, {})
                color = field_config.get("color", colors[i % len(colors)])
                marker_symbol = field_config.get("emoji", "�")
                unit = field_config.get("unit", "")
                label_text = f"{marker_symbol} {field}"
                if unit:
                    label_text += f" ({unit})"
                
                # 그래프 그리기
                line = current_ax.plot(xs, ys, color=color, 
                                     label=label_text, marker='o', markersize=3, 
                                     linewidth=2.5, alpha=0.8)
                
                # Y축 색상을 그래프 색상과 동일하게 설정
                current_ax.tick_params(axis='y', labelcolor=color, colors=color)
                # Y축 레이블 제거 (숫자만 표시)
                current_ax.set_ylabel('')
                current_ax.spines['right'].set_color(color)
                if plot_count == 0:
                    current_ax.spines['left'].set_color(color)
                
                # Y축 범위 고정
                if field == "SOC":
                    current_ax.set_ylim(0, 100)
                elif field == "유량":
                    current_ax.set_ylim(0, 100)
                elif field == "퓨얼링압력":
                    current_ax.set_ylim(0, 800)
                
                axes_list.append((current_ax, label_text, color))
                plot_count += 1
        
        # X축 커서 추가 (활성화된 경우에만)
        if cursor_active[0] and xs and plot_count > 0:
            # clear() 호출로 이미 모든 라인이 제거되었으므로 바로 새 커서 생성
            global_cursor_idx = cursor_idx[0]
            recent_start_idx = len(data_rows) - len(recent_data)
            local_cursor_idx = global_cursor_idx - recent_start_idx
            
            if 0 <= local_cursor_idx < len(xs):
                cursor_time = xs[local_cursor_idx]
                # 새 커서 라인 생성 (clear 후이므로 안전)
                cursor_line = ax_graph.axvline(x=cursor_time, color='red', linestyle='-', 
                                             linewidth=2, alpha=0.8, zorder=10)
    
    # 기본 축 설정
    ax_graph.set_xlabel("시간 (초)", fontsize=12, fontweight='bold')
    ax_graph.set_title(f"실시간 모니터링 - {'ON' if data_on[0] else 'OFF'}", 
                      fontsize=14, fontweight='bold')
    
    # X축을 분:초 형태로 표시 (0:00, 0:30, 1:00...)
    from matplotlib.ticker import MaxNLocator
    ax_graph.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax_graph.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_time(x)))
    
    # 범례를 모든 축에서 수집해서 하나로 통합
    if plot_count > 0:
        all_lines = []
        all_labels = []
        for ax_item, label, color in axes_list:
            lines = ax_item.get_lines()
            if lines:
                # 각 축의 첫 번째 라인만 추가 (커서 라인 제외)
                for line in lines:
                    if line.get_color() != 'red':  # 커서 라인 제외
                        all_lines.append(line)
                        all_labels.append(label)
                        break  # 각 축당 하나의 라인만
        
        if all_lines:
            # 범례를 버튼과 같은 높이에 배치
            ax_graph.legend(all_lines, all_labels, bbox_to_anchor=(0.96, 1.12), 
                           loc='upper right', fontsize=9, ncol=2, framealpha=0.9,
                           columnspacing=0.5, handlelength=1.5)
    
    # 격자는 기본 축에만
    ax_graph.grid(True, linestyle=':', alpha=0.4, zorder=0)
    
    # X축 범위 설정 (시간이 계속 늘어나도록)
    if xs:
        x_min = min(xs)
        x_max = max(xs)
        x_range = x_max - x_min
        if x_range > 0:
            # 데이터 범위에 여백 추가
            padding = x_range * 0.02
            ax_graph.set_xlim(x_min - padding, x_max + padding)
        else:
            ax_graph.set_xlim(0, 10)  # 기본 범위
    else:
        ax_graph.set_xlim(0, 50)  # 초기 범위
    
    # 레이아웃은 이미 subplots_adjust로 설정됨
    
    # LIVE 버튼 색상 업데이트 (ON 상태이고 데이터 수신 중일 때만 색상 표시)
    if data_on[0] and len(data_rows) > 0:
        btn_reset.color = 'lightblue'
    else:
        btn_reset.color = 'white'
    btn_reset.ax.set_facecolor(btn_reset.color)
    
    fig.canvas.draw_idle()

def on_slider(val):
    idx = int(val)
    cursor_active[0] = True  # 슬라이더 사용시에도 커서 활성화
    cursor_idx[0] = idx

def on_click(event):
    """그래프 클릭 시 커서 활성화 및 이동"""
    global all_graph_axes
    
    # 그래프 영역에서 클릭 감지 (모든 축 포함)
    is_graph_click = False
    if event.inaxes:
        # 메인 그래프 축인지 확인
        if event.inaxes == ax_graph:
            is_graph_click = True
        # 또는 twin axis들 중 하나인지 확인
        elif event.inaxes in all_graph_axes:
            is_graph_click = True
    
    if is_graph_click and event.xdata is not None:
        with lock:
            if not data_rows:
                return
            
            # 첫 클릭시 커서 활성화
            cursor_active[0] = True
            
            # 클릭한 x좌표에서 가장 가까운 데이터 포인트 찾기 (전체 데이터 사용)
            if not data_rows:
                return
            xs = [row[0] - data_rows[0][0] for row in data_rows]  # 전체 데이터 기준
            
            # 클릭 위치와 가장 가까운 인덱스 찾기
            closest_idx = min(range(len(xs)), key=lambda i: abs(xs[i] - event.xdata))
            global_idx = closest_idx
            
            cursor_idx[0] = global_idx
            
            # 슬라이더가 있으면 동기화 (실시간 업데이트는 중단하지 않음)
            if slider is not None:
                slider.set_val(global_idx)
            
            # 상태 패널만 업데이트 (그래프는 periodic_update에서 계속 처리)


def update_all():
    # 항상 그래프는 업데이트 (실시간 표시 유지)
    update_graph()
    
    # 현재 값 패널 업데이트 (실시간으로 최신 데이터 표시)
    update_current_values()
    
    with lock:
        data_count = len(data_rows)
    
    if data_count > 0:
        # 슬라이더 범위 업데이트
        if slider is not None:
            slider.valmax = max(1, data_count-1)
            slider.ax.set_xlim(0, slider.valmax)
            
            # 커서가 비활성화 상태이고 ON 상태일 때만 자동으로 최신으로 이동
            if data_on[0] and not cursor_active[0]:
                cursor_idx[0] = data_count - 1
                slider.set_val(data_count-1)
        
        # 상태 패널 업데이트 (ON 상태이거나 커서 활성화시에만)
        if data_on[0] or cursor_active[0]:
            if cursor_active[0]:
                # 커서 모드: 커서 위치의 데이터 표시
                update_state_panel(cursor_idx[0])
            else:
                # 실시간 모드: 최신 데이터 표시
                update_state_panel(None)


def periodic_update_callback():
    """고성능 타이머 콜백 함수 (성능 진단 포함)"""
    global slider
    
    # OFF 상태이고 커서도 비활성화면 업데이트 안함
    if not data_on[0] and not cursor_active[0]:
        return
    
    # 성능 측정 시작
    callback_start_time = time.perf_counter()
    
    try:
        with lock:
            data_count = len(data_rows)
        
        # 슬라이더 동적 생성 (필요시에만)
        if slider is None and data_count > 1:
            # 하단 슬라이더 영역에 배치
            ax_slider = plt.axes([0.15, 0.02, 0.7, 0.03])
            slider = Slider(ax_slider, '시간축 커서', 0, max(1, data_count-1), 
                           valinit=data_count-1, valstep=1, valfmt='%d')
            slider.on_changed(on_slider)
            print("🎛️ 슬라이더 생성 완료")
        
        # 📈 메인 업데이트 실행
        update_all()
        
        # 성능 통계 (10초마다)
        callback_end_time = time.perf_counter()
        callback_duration = (callback_end_time - callback_start_time) * 1000  # ms
        
        if not hasattr(periodic_update_callback, 'last_perf_report'):
            periodic_update_callback.last_perf_report = time.time()
            periodic_update_callback.callback_times = []
        
        periodic_update_callback.callback_times.append(callback_duration)
        
        # 10초마다 성능 리포트
        current_time = time.time()
        if current_time - periodic_update_callback.last_perf_report >= 10.0:
            avg_time = sum(periodic_update_callback.callback_times) / len(periodic_update_callback.callback_times)
            max_time = max(periodic_update_callback.callback_times)
            
            print(f"GUI 성능: 평균 {avg_time:.1f}ms, 최대 {max_time:.1f}ms, 데이터 {data_count}개")
            
            # 성능 경고
            if avg_time > 100:  # 100ms 이상이면 경고
                print("GUI 응답 속도 저하 감지 - 데이터 정리 권장")
            elif avg_time < 50:  # 50ms 이하면 양호
                print("GUI 응답 속도 양호")
            
            # 리스트 초기화
            periodic_update_callback.callback_times = []
            periodic_update_callback.last_perf_report = current_time
            
    except Exception as e:
        print(f"periodic_update_callback 오류: {e}")
        import traceback
        traceback.print_exc()

def periodic_update():
    """고성능 타이머 설정 (정밀도 향상)"""
    global update_timer
    # 초기 업데이트
    try:
        update_all()
        
        # 그래프 업데이트 주기: 1초(1000ms) 고정
        interval = 1000  # 1초
        
        # 정밀 타이머 설정 (중복 방지 강화)
        if update_timer is None:
            update_timer = fig.canvas.new_timer(interval=interval)
            update_timer.add_callback(periodic_update_callback)
            update_timer.start()
            print(f"⏱️  정밀 타이머 시작: {interval}ms 간격")
        elif hasattr(update_timer, 'running') and not update_timer.running:
            # 타이머가 있지만 멈춰있으면 재시작
            update_timer.start()
            print(f"🔄 타이머 재시작: {interval}ms")
        else:
            print("타이머 이미 실행 중 (중복 실행 방지)")
    except Exception as e:
        print(f"periodic_update 오류: {e}")
        import traceback
        traceback.print_exc()

# ON/OFF 버튼 콜백
def on_on(event):
    global data_rows, current_sequence_index, udp_thread, last_received_data
    # 처음부터 다시 시작: 데이터 및 CSV 파일 초기화
    with lock:
        data_rows.clear()
    cursor_active[0] = False
    cursor_idx[0] = 0
    current_state[0] = "대기중"
    
    # 메모리 데이터만 초기화 (실시간 CSV 파일 사용 안함)
    print("데이터 메모리 초기화 완료")
    
    # 완전한 데이터 초기화 - 모든 이전 상태 제거
    with duplicate_prevention_lock:
        last_received_data["content"] = ""
        last_received_data["timestamp"] = 0
    
    # 상태 순서 초기화
    current_sequence_index[0] = 0  # IDLE부터 다시 시작
    print("🔄 상태 순서 초기화: IDLE부터 시작")
    
    # data_rows 완전 초기화 (global 선언 없이)
    with lock:
        data_rows.clear()
        print("모든 이전 데이터 완전 삭제")
    
    # 기존 virtual_data.txt 파일 완전 정리 (반복적으로)
    import os, time  # os 모듈 import를 여기로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    virtual_data_file = os.path.join(script_dir, "virtual_data.txt")
    
    # 강력한 파일 정리 - 여러 번 시도
    for i in range(5):  # 5번 시도
        if os.path.exists(virtual_data_file):
            try:
                os.remove(virtual_data_file)
                print(f"🗑️ virtual_data.txt 파일 정리됨 (시도 {i+1})")
            except:
                pass
        time.sleep(0.1)  # 0.1초 대기 후 재시도
    
    # 최종 확인
    if not os.path.exists(virtual_data_file):
        print("virtual_data.txt 파일 완전히 정리 확인됨")
    else:
        print("virtual_data.txt 파일 정리 실패 - 강제 무시 모드 활성화")
    
    data_on[0] = True
    
    # 상태 순서 인덱스 초기화 (중요!)
    current_sequence_index[0] = 0
    print("ON: 데이터 수신 시작 (새로 시작) - 상태 순서 초기화")
    
    # 그래프 화면 완전 초기화
    clear_all_graphs()
    
    # UDP 수신기 재시작 (기존 스레드 강제 정리)
    if udp_thread is not None:
        if udp_thread.is_alive():
            print("기존 UDP 수신기 종료 대기 중...")
            # data_on을 False로 설정하여 기존 스레드 종료 유도
            old_data_on = data_on[0]
            data_on[0] = False
            udp_thread.join(timeout=2.0)  # 최대 2초 대기
            data_on[0] = old_data_on  # 원복
        udp_thread = None
    
    # 새 UDP 수신기 시작
    udp_thread = threading.Thread(target=udp_receiver, daemon=True)
    udp_thread.start()
    print("새 UDP 수신기 스레드 시작됨")
    
    # disp.py에 UDP ON 신호 전송
    try:
        # 기존 stop 신호 제거 (os는 이미 import됨)
        signal_dir = os.path.dirname(os.path.abspath(__file__))
        stop_signal_path = os.path.join(signal_dir, "stop_signal.txt")
        start_signal_path = os.path.join(signal_dir, "start_signal.txt")
        
        if os.path.exists(stop_signal_path):
            os.remove(stop_signal_path)
        
        # UDP로 ON 신호 전송 (disp.py에게)
        try:
            signal_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            signal_sock.sendto(b"ON", (DISP_IP, CONTROL_PORT))
            signal_sock.close()
            print(f"disp.py({DISP_IP}:{CONTROL_PORT})에 ON 신호 전송")
        except Exception as udp_error:
            print(f"UDP 신호 전송 실패: {udp_error}")
            # Fallback: 파일 신호
            with open(start_signal_path, "w") as f:
                f.write("start\n")
            print(f"📁 Fallback: 파일 신호 생성 {start_signal_path}")
    except Exception as e:
        print("신호 파일 생성 오류:", e)

# 현재 데이터를 CSV 파일로 저장 (가독성 좋은 형태)
def save_current_data(custom_filename=None):
    if not data_rows:
        print("저장할 데이터가 없습니다.")
        return
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if custom_filename:
        # 사용자 지정 파일명 사용
        if not custom_filename.endswith('.csv'):
            filename = f"{custom_filename}.csv"
        else:
            filename = custom_filename
    else:
        # 기본 타임스탬프 파일명
        filename = f"monitoring_data_{timestamp}.csv"
    
    try:
        import csv
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:  # BOM 추가로 한글 깨짐 방지
            writer = csv.writer(f)
            
            # 전체 파일 헤더
            writer.writerow(['수소 충전소 모니터링 데이터'])
            writer.writerow([f'생성 시간: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([f'총 데이터 수: {len(data_rows)}개'])
            writer.writerow([])  # 빈 줄
            
            # 상태별로 데이터 분리 및 저장
            current_state = None
            state_data = []
            
            for row in data_rows:
                # 시간 스탬프를 초 단위로 변환 (시작 시간 기준)
                start_timestamp = data_rows[0][0] if data_rows else 0
                relative_time = int(row[0] - start_timestamp)
                
                if len(row) >= 2 and isinstance(row[1], dict):
                    row_state = row[1].get('STATE', 'UNKNOWN')
                    data_dict = row[1]
                    
                    # 상태가 변경되었을 때
                    if current_state != row_state:
                        # 이전 상태 데이터 저장
                        if current_state is not None and state_data:
                            write_clean_state_section(writer, current_state, state_data)
                            writer.writerow([])  # 상태 간 빈 줄
                        
                        # 새 상태 시작
                        current_state = row_state
                        state_data = [(relative_time, data_dict)]
                    else:
                        state_data.append((relative_time, data_dict))
            
            # 마지막 상태 데이터 저장
            if current_state is not None and state_data:
                write_clean_state_section(writer, current_state, state_data)
        
        print(f"데이터가 {filename}에 저장되었습니다. (총 {len(data_rows)}개 레코드)")
    except Exception as e:
        print(f"데이터 저장 오류: {e}")

def write_clean_state_section(writer, state, state_data):
    """상태별 데이터 섹션을 가독성 좋게 작성"""
    # 상태명과 설명 작성
    state_names = {
        "IDLE": "대기",
        "STARTUP": "시작", 
        "MAIN_FUELING": "충전",
        "SHUTDOWN": "종료"
    }
    
    writer.writerow([f"=== {state_names.get(state, state)} 상태 ==="])
    
    if not state_data:
        writer.writerow(["데이터 없음"])
        return
    
    # 첫 번째 데이터에서 숫자형 필드들만 추출
    first_time, first_data = state_data[0]
    numeric_fields = []
    
    # 숫자형 데이터만 필터링 (상태 제외)
    for field, value in first_data.items():
        if field == 'STATE':
            continue
        try:
            float(value)  # 숫자 변환 가능한지 테스트
            numeric_fields.append(field)
        except (ValueError, TypeError):
            pass  # 숫자가 아닌 필드는 제외
    
    if not numeric_fields:
        writer.writerow(["숫자형 데이터 없음"])
        return
    
    # 깔끔한 헤더 작성 (시간 + 숫자형 필드들만)
    header = ['시간(초)'] + numeric_fields
    writer.writerow(header)
    
    # 데이터 작성 (숫자 값들만)
    for time_val, data_dict in state_data:
        row = [time_val]
        for field in numeric_fields:
            value = data_dict.get(field, '')
            row.append(value)
        writer.writerow(row)

def on_off(event):
    global data_rows, current_sequence_index
    if not data_on[0]:  # 이미 OFF 상태면 무시
        print("이미 OFF 상태입니다.")
        return
        
    data_on[0] = False
    current_state[0] = "대기중"
    
    # 상태 순서 인덱스 초기화 (중요!)
    current_sequence_index[0] = 0
    
    # cursor_active는 OFF 후에도 유지 (커서 기능 계속 사용 가능)
    print("OFF: 데이터 수신 중지 - 상태 순서 초기화")
    
    # 데이터 저장 여부 확인 (PyInstaller 빌드 안전)
    if data_rows:  # 저장할 데이터가 있을 때만 물어봄
        try:
            # PyInstaller 환경에서 안전한 tkinter import
            import tkinter as tk
            from tkinter import messagebox
            
            # 임시 루트 윈도우 생성 (보이지 않게)
            root = tk.Tk()
            root.withdraw()  # 창 숨기기
            
            # 저장 여부 묻기
            result = messagebox.askyesno("데이터 저장", 
                                       f"수신된 데이터({len(data_rows)}개 레코드)를\nCSV 파일로 저장하시겠습니까?",
                                       icon='question')
            
            # 임시 윈도우 제거
            root.destroy()
            
            if result:  # 예를 선택한 경우
                # 파일명 입력 받기
                from tkinter import simpledialog
                
                # 기본 파일명 생성
                import datetime
                default_name = f"monitoring_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 파일명 입력 대화상자
                custom_name = simpledialog.askstring(
                    "파일명 입력",
                    "저장할 파일명을 입력하세요:\\n(확장자 .csv는 자동 추가됩니다)",
                    initialvalue=default_name
                )
                
                if custom_name:  # 파일명 입력했으면 저장
                    # 파일명에서 경로 구분자 제거 (보안 및 오류 방지)
                    custom_name = custom_name.replace('/', '_').replace('\\', '_').replace(':', '_')
                    save_current_data(custom_name)
                else:
                    print("파일명을 입력하지 않아 저장을 취소했습니다.")
            else:
                print("데이터 저장을 취소했습니다.")
                
        except Exception as tk_error:
            # tkinter 실패 시 콘솔에서 입력 받기
            print(f"GUI 대화상자 실패: {tk_error}")
            print(f"수신된 데이터({len(data_rows)}개 레코드)를 CSV 파일로 저장하시겠습니까?")
            user_input = input("저장하려면 'y' 또는 'yes'를 입력하세요: ").lower().strip()
            if user_input in ['y', 'yes', 'Y', 'YES']:
                # 파일명 입력 받기
                import datetime
                default_name = f"monitoring_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"기본 파일명: {default_name}.csv")
                custom_name = input("저장할 파일명을 입력하세요 (엔터: 기본값 사용): ").strip()
                
                if custom_name:
                    # 파일명에서 경로 구분자 제거 (보안 및 오류 방지)
                    custom_name = custom_name.replace('/', '_').replace('\\', '_').replace(':', '_')
                    save_current_data(custom_name)
                else:
                    save_current_data(default_name)
            else:
                print("데이터 저장을 취소했습니다.")
    
    # 임시 CSV 파일 정리 (있다면)
    try:
        import os
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            print("임시 CSV 파일 정리 완료")
    except Exception as e:
        print(f"임시 파일 정리 오류: {e}")
    
    # OFF 시에는 데이터를 유지 (그래프 화면 유지를 위해)
    print("데이터는 유지됨 (그래프 화면 유지)")
    
    # UDP 스레드 완전 종료 대기
    global udp_thread
    if udp_thread is not None and udp_thread.is_alive():
        print("UDP 수신기 종료 대기 중...")
        udp_thread.join(timeout=3.0)  # 최대 3초 대기
        if udp_thread.is_alive():
            print("UDP 스레드 강제 종료 준비")
        udp_thread = None
    
    # UDP로 disp.py에 OFF 신호 전송
    try:
        control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        control_socket.sendto(b"OFF", (DISP_IP, CONTROL_PORT))
        control_socket.close()
        print(f"disp.py({DISP_IP}:{CONTROL_PORT})에 OFF 신호 전송")
    except Exception as e:
        print(f"UDP STOP 신호 전송 실패: {e}")
        # 폴백: 파일 기반 신호
        try:
            import os
            # start 신호 제거
            if os.path.exists("start_signal.txt"):
                os.remove("start_signal.txt")
                print("start 신호 파일 제거됨")
            
            # stop 신호 생성하여 disp.py에 중지 신호 전달
            with open("stop_signal.txt", "w") as f:
                f.write("stop\n")
            print("stop 신호 파일 생성됨 (폴백)")
            
        except Exception as e2:
            print("파일 기반 신호 처리 오류:", e2)

# 저장된 데이터 불러서 재생
def replay_saved_data():
    """저장된 CSV 파일을 불러와서 그래프로 표시"""
    from tkinter import filedialog
    import tkinter as tk
    
    # 파일 선택 다이얼로그
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기
    filename = filedialog.askopenfilename(
        title="CSV 파일 선택",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialdir="."
    )
    root.destroy()
    
    if not filename:
        print("파일 선택 취소됨")
        return
    
    try:
        with open(filename, newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if not rows:
            print('저장된 데이터 없음')
            return
        
        # 상태별 데이터 파싱
        loaded_data = []
        current_section = None
        header_fields = []
        
        for row in rows:
            if not row or not row[0]:
                continue
            
            # 상태 섹션 시작 감지
            if row[0].startswith('==='):
                current_section = row[0].strip('= ')
                continue
            
            # 헤더 행 감지 (시간(초)로 시작)
            if row[0] == '시간(초)':
                header_fields = row[1:]  # 시간 제외한 필드명들
                continue
            
            # 메타데이터 행 건너뛰기
            if any(x in row[0] for x in ['수소 충전소', '생성 시간', '총 데이터 수', '데이터 없음', '숫자형 데이터']):
                continue
            
            # 실제 데이터 행 파싱
            if header_fields and current_section:
                try:
                    time_val = float(row[0])
                    data_dict = {'STATE': current_section.split()[0]}  # 상태명만 추출
                    
                    # 각 필드 값 추가
                    for i, field in enumerate(header_fields):
                        if i + 1 < len(row) and row[i + 1]:
                            try:
                                data_dict[field] = float(row[i + 1])
                            except ValueError:
                                data_dict[field] = row[i + 1]
                    
                    # data_rows 형식으로 변환: [timestamp, data_dict]
                    loaded_data.append([time_val, data_dict])
                except (ValueError, IndexError) as e:
                    continue
        
        if not loaded_data:
            print('유효한 데이터를 찾을 수 없습니다.')
            return
        
        # 로드된 데이터의 필드 확인
        sample_fields = set()
        for row in loaded_data[:5]:  # 처음 5개 행에서 필드 확인
            if len(row) > 1 and isinstance(row[1], dict):
                sample_fields.update(row[1].keys())
        print(f"로드된 데이터 필드: {sample_fields}")
        
        # CSV에서는 상대 시간(초)으로 저장되어 있으므로 절대 타임스탬프로 변환
        import time as time_module
        base_time = time_module.time()  # 현재 시간을 기준점으로
        for row in loaded_data:
            row[0] = base_time + row[0]  # 상대 시간을 절대 시간으로 변환
        
        print(f"첫 데이터: {loaded_data[0]}")
        print(f"마지막 데이터: {loaded_data[-1]}")
        
        # 기존 데이터를 로드된 데이터로 교체
        global data_rows, cursor_idx, cursor_active, slider
        
        with lock:
            data_rows.clear()
            data_rows.extend(loaded_data)
        
        # 커서를 처음으로 설정
        cursor_idx[0] = 0
        cursor_active[0] = True
        
        print(f"CSV 파일 로드 완료: {filename}")
        print(f"총 {len(loaded_data)}개 레코드 로드됨")
        print(f"첫 5개 데이터 샘플:")
        for i, row in enumerate(loaded_data[:5]):
            print(f"  [{i}] time={row[0]:.2f}, data={row[1]}")
        
        # 슬라이더 범위 업데이트
        if slider is not None:
            slider.valmax = max(1, len(loaded_data) - 1)
            slider.ax.set_xlim(0, slider.valmax)
            slider.set_val(0)
        
        # 전체 업데이트 (상태 패널, 현재 값, 그래프)
        update_all()
        
        # 강제로 화면 새로고침
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        print("CSV 로드 및 화면 업데이트 완료")
        
    except Exception as e:
        import traceback
        print(f"CSV 파일 로드 오류: {e}")
        traceback.print_exc()


# 화면 크기 변경 시 레이아웃 자동 조정 함수
def on_resize(event):
    """화면 크기 변경 시 레이아웃 비율 유지"""
    try:
        # 그리드 간격과 여백 재조정 - 비율 유지
        gs.update(hspace=0.08, wspace=0.10)
        # 왼쪽으로 이동된 레이아웃 유지
        fig.subplots_adjust(left=0.02, right=0.95, top=0.95, bottom=0.05)
        fig.canvas.draw_idle()
    except Exception as e:
        print(f"레이아웃 조정 오류: {e}")

# 화면 크기 변경 이벤트 연결
fig.canvas.mpl_connect('resize_event', on_resize)

# ON/OFF 버튼 생성 (왼쪽으로 이동)
ax_btn_on = plt.axes([0.30, 0.93, 0.07, 0.04])
ax_btn_off = plt.axes([0.38, 0.93, 0.07, 0.04])
ax_btn_reset = plt.axes([0.46, 0.93, 0.08, 0.04])  # 커서 리셋 버튼
ax_btn_load = plt.axes([0.55, 0.93, 0.08, 0.04])   # 불러오기 버튼 (SAVE 위치로 이동)

btn_on = Button(ax_btn_on, 'ON', color='lightgreen', hovercolor='green')
btn_off = Button(ax_btn_off, 'OFF', color='lightcoral', hovercolor='red')
btn_reset = Button(ax_btn_reset, 'LIVE', color='white', hovercolor='blue')  # 기본은 색상 없음
btn_load = Button(ax_btn_load, 'LOAD', color='lightgray', hovercolor='gray')

def on_reset_cursor(event):
    """커서 비활성화하고 실시간 모드로 전환"""
    cursor_active[0] = False
    if data_rows:
        cursor_idx[0] = len(data_rows) - 1

def on_load_button(event):
    """불러오기 버튼 클릭 시 CSV 파일 로드"""
    replay_saved_data()

btn_on.on_clicked(on_on)
btn_off.on_clicked(on_off)
btn_reset.on_clicked(on_reset_cursor)
btn_load.on_clicked(on_load_button)

# 마우스 클릭 이벤트 연결
fig.canvas.mpl_connect('button_press_event', on_click)


# 타이머 시작 및 메인 루프
try:
    print("모니터링 시스템 시작 중...")
    periodic_update()
    print("그래프 창이 표시되었습니다. 창을 닫으면 프로그램이 종료됩니다.")
    
    # matplotlib 창이 열린 상태로 유지
    plt.show(block=True)
    
except KeyboardInterrupt:
    print("\n사용자에 의해 종료됨")
except Exception as e:
    import traceback
    print(f"[오류] {e}")
    traceback.print_exc()
    input("엔터를 누르면 종료합니다...")
finally:
    print("모니터링 시스템 종료")
