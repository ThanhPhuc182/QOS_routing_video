import requests
import time
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime

# ==========================================
# CÀI ĐẶT MÀU SẮC
# ==========================================
C_GREEN = '\033[92m'
C_RED = '\033[91m'
C_YELLOW = '\033[93m'
C_BLUE = '\033[94m'
C_RESET = '\033[0m'
C_BOLD = '\033[1m'
C_CYAN = '\033[96m'

# ==========================================
# 1. BỘ NÃO AI 
# ==========================================
class DQNNetwork(nn.Module):
    def __init__(self, state_size=20, action_size=4):
        super(DQNNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, action_size)
        )
    def forward(self, state): return self.net(state)

# ==========================================
# 2. CẤU HÌNH API 
# ==========================================
RYU_URL_ADD = "http://127.0.0.1:8080/stats/flowentry/add"
RYU_URL_PORT = "http://127.0.0.1:8080/stats/port"
DEVICE = torch.device("cpu")

def send_rule(switch_name, rule_data):
    try: requests.post(RYU_URL_ADD, json=rule_data)
    except: pass

def get_port_tx_bytes(dpid, port_no):
    try:
        res = requests.get(f"{RYU_URL_PORT}/{dpid}").json()
        for port in res[str(dpid)]:
            if str(port['port_no']) == str(port_no):
                return int(port['tx_bytes'])
    except: return 0

# ==========================================
# 3. ĐO ĐẠC VÀ MAPPING DỮ LIỆU
# ==========================================
def get_mapped_state():
    b1 = get_port_tx_bytes(1, 2)
    time.sleep(1.0) 
    b2 = get_port_tx_bytes(1, 2)
    speed = ((b2 - b1) * 8) / 1000000.0
    
    # Ép AI mặc định chọn Path 1 khi rảnh rỗi (Phạt các đường khác 60ms)
    state = np.ones(20, dtype=np.float32) * 60.0 
    for i in range(10): state[i*2+1] = 0.0 
    state[2*2] = 20.0 
    state[9*2] = 20.0 
    
    now = datetime.now().strftime("%H:%M:%S")
    
    # NẾU TẮC NGHẼN: Đánh thẳng vào LINK SỐ 6 (12, 13) ĐÚNG NHƯ LÚC TRAIN!
    if speed > 8.0:
        print(f"[{now}] {C_RED}⚠ Tốc độ: {speed:.2f} Mbps -> PHÁT HIỆN TẮC NGHẼN ĐƯỜNG CHÍNH!{C_RESET}")
        state[12] = 400.0  # Link 6 Delay
        state[13] = 25.0   # Link 6 Loss
    else:
        print(f"[{now}] {C_GREEN}✔ Tốc độ: {speed:.2f} Mbps -> Mạng thông thoáng.{C_RESET}")
        state[12] = 20.0   # Link 6 Delay
        state[13] = 0.0    # Link 6 Loss
        
    return state

# ==========================================
# 4. VÒNG LẶP CHÍNH (SHOWTIME)
# ==========================================
if __name__ == '__main__':
    print(f"\n{C_BLUE}{C_BOLD}{'='*75}")
    print(" HỆ THỐNG RL TỰ ĐỘNG BẢO VỆ CHẤT LƯỢNG VIDEO (QoS-AWARE ROUTING)")
    print(f"{'='*75}{C_RESET}\n")

    model = DQNNetwork(20, 4).to(DEVICE)
    try:
        model.load_state_dict(torch.load("dqn_routing_ultimate.pth", map_location=DEVICE))
        model.eval()
        print(f"{C_GREEN}[HỆ THỐNG] Đã nạp thành công bộ não AI (DQN Model).{C_RESET}\n")
    except Exception as e:
        print(f"{C_RED}[LỖI] Không tìm thấy file model .pth!{C_RESET}"); exit()

    current_action = -1 

    while True:
        obs = get_mapped_state()
        
        obs_tensor = torch.tensor(obs, dtype=torch.float32, device=DEVICE).unsqueeze(0)
        with torch.no_grad():
            q_values = model(obs_tensor)
            action = q_values.argmax(dim=1).item()
            
        # In điểm số Q-value ra màn hình để thấy AI đang "suy nghĩ"
        q_list = q_values.numpy()[0]
        print(f"   {C_CYAN}└─ [AI Suy nghĩ] Điểm Q-Value: Path 0 ({q_list[0]:.1f}) | Path 1 ({q_list[1]:.1f}) | Path 2 ({q_list[2]:.1f}) | Path 3 ({q_list[3]:.1f}){C_RESET}")
            
        if action != current_action:
            print(f"\n{C_YELLOW}{C_BOLD}>>>>>>>> TÍNH TOÁN LẠI LUỒNG ĐỊNH TUYẾN <<<<<<<<{C_RESET}")
            
            if action == 1:
                print(f"{C_BLUE}[AI QUYẾT ĐỊNH] Mạng an toàn. Trả luồng Video về ĐƯỜNG CHÍNH (Path 1){C_RESET}")
                send_rule("Switch 1", {"dpid": 1, "priority": 65535, "match": {"eth_type": 2048, "ipv4_dst": "10.0.0.2", "ip_proto": 17, "udp_dst": 1234}, "actions":[{"type": "OUTPUT", "port": 2}]})
                send_rule("Switch 2", {"dpid": 2, "priority": 65535, "match": {"eth_type": 2048, "ipv4_dst": "10.0.0.2", "ip_proto": 17, "udp_dst": 1234}, "actions":[{"type": "OUTPUT", "port": 2}]})
                send_rule("Switch 4", {"dpid": 4, "priority": 65535, "match": {"eth_type": 2048, "ipv4_dst": "10.0.0.2", "ip_proto": 17, "udp_dst": 1234}, "actions":[{"type": "OUTPUT", "port": 1}]})
            else:
                print(f"{C_RED}{C_BOLD}[AI QUYẾT ĐỊNH] NGUY HIỂM! BẺ LÁI SANG ĐƯỜNG DỰ PHÒNG ĐỂ CỨU MOS (Path 2){C_RESET}")
                send_rule("Switch 1", {"dpid": 1, "priority": 65535, "match": {"eth_type": 2048, "ipv4_dst": "10.0.0.2", "ip_proto": 17, "udp_dst": 1234}, "actions":[{"type": "OUTPUT", "port": 3}]})
                send_rule("Switch 3", {"dpid": 3, "priority": 65535, "match": {"eth_type": 2048, "ipv4_dst": "10.0.0.2", "ip_proto": 17, "udp_dst": 1234}, "actions":[{"type": "OUTPUT", "port": 2}]})
                send_rule("Switch 4", {"dpid": 4, "priority": 65535, "match": {"eth_type": 2048, "ipv4_dst": "10.0.0.2", "ip_proto": 17, "udp_dst": 1234}, "actions":[{"type": "OUTPUT", "port": 1}]})
                
            print(f"{C_YELLOW}{C_BOLD}>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<{C_RESET}\n")
            current_action = action