import sys
import subprocess

# Tự động kiểm tra và cài đặt thư viện nếu máy chưa có
REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "matplotlib": "matplotlib"
}

for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"[Auto-Setup] Chưa tìm thấy thư viện '{package_name}'. Đang tự động cài đặt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"[Auto-Setup] Đã cài đặt thành công '{package_name}'!")
        except Exception as e:
            print(f"[Lỗi] Không thể tự động cài {package_name}: {e}")
            print(f"Vui lòng chạy lệnh: pip install -r requirements.txt")
            sys.exit(1)

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

class SystemHardwareConfig:
    def __init__(self):
        self.M = 2            
        self.N = 40           
        self.Pt_dBm = 36    
        self.sigma2_dBm = -94 
        
        self.Pt = 10**((self.Pt_dBm - 30) / 10)
        self.sigma2 = 10**((self.sigma2_dBm - 30) / 10)
        
        self.C0 = 10**(-40 / 10)
        self.alpha_AP_IRS = 2.2 
        self.alpha_IRS_user = 2.8
        self.alpha_AP_user = 3.8 
        
        self.num_monte_carlo = 30  
        
        self.f = 2.4e9                 
        self.omega = 2 * np.pi * self.f
        self.Z0 = 377.0                
        
        self.beta_min = 0.2
        self.k = 1.6
        self.phi = 0.43 * np.pi
        self.max_iter_AO = 300
        
        self.L1_bounds = (2e-9, 10e-9)   
        self.L2_bounds = (1e-9, 5e-9)   
        self.C_bounds  = (0.2e-12, 5e-12) 
        self.R_bounds  = (0.1, 0.5) 
        
        self.swarm_size = 65      
        self.max_iter_PSO = 400    
        self.w_max = 0.9
        self.w_min = 0.3
        self.c1 = 1.5
        self.c2 = 2.5 

def path_loss(dist, alpha, C0):
    return C0 * (dist ** (-alpha))

def beta_fn(theta, cfg):
    return (1 - cfg.beta_min) * ((np.sin(theta - cfg.phi) + 1) / 2)**cfg.k + cfg.beta_min

def f_theta(theta, Psi_nn, phi_n, cfg):
    beta = beta_fn(theta, cfg)
    return (beta**2) * np.real(Psi_nn) + beta * np.abs(phi_n) * np.cos(np.angle(phi_n) - theta)

def calculate_v_from_hardware(L1, L2, C, R, cfg):
    j_omega = 1j * cfg.omega
    Z_series = j_omega * L2 + 1.0 / (j_omega * C) + R
    Z_L1 = j_omega * L1
    Z_n = (Z_L1 * Z_series) / (Z_L1 + Z_series)
    v_n = (Z_n - cfg.Z0) / (Z_n + cfg.Z0)
    return v_n

def optimize_IRS_Ideal_AO(hd, hr, G, cfg):
    theta = np.random.choice([np.pi, -np.pi], cfg.N)
    v = np.exp(1j * theta)
    Phi = np.diag(hr.conj()) @ G
    Psi = Phi @ Phi.conj().T
    hd_hat = Phi @ hd
    
    for _ in range(cfg.max_iter_AO):
        v_old = np.copy(v)
        for n in range(cfg.N):
            phi_n = np.sum(Psi[n, :] * v) - Psi[n, n] * v[n] + hd_hat[n]
            theta_opt = np.angle(phi_n)
            theta[n] = theta_opt
            v[n] = np.exp(1j * theta_opt)
        if np.linalg.norm(v - v_old) < 1e-4: break
    return v

def optimize_IRS_AO_Gốc(hd, hr, G, cfg):
    theta = np.random.choice([np.pi, -np.pi], cfg.N)
    v = np.array([beta_fn(t, cfg) * np.exp(1j * t) for t in theta])
    Phi = np.diag(hr.conj()) @ G
    Psi = Phi @ Phi.conj().T
    hd_hat = Phi @ hd
    
    for _ in range(cfg.max_iter_AO):
        v_old = np.copy(v)
        for n in range(cfg.N):
            phi_n = np.sum(Psi[n, :] * v) - Psi[n, n] * v[n] + hd_hat[n]
            arg_phi_n = np.angle(phi_n)
            lamda = 0 if arg_phi_n >= 0 else 1
            theta_A, theta_C = arg_phi_n, ((-1)**lamda) * np.pi
            theta_B = (theta_A + theta_C) / 2
            
            f1 = f_theta(theta_A, Psi[n, n], phi_n, cfg)
            f2 = f_theta(theta_B, Psi[n, n], phi_n, cfg)
            f3 = f_theta(theta_C, Psi[n, n], phi_n, cfg)
            
            tu_so = ((-1)**lamda)*np.pi*(3*f1 - 4*f2 + f3) + arg_phi_n*(f1 - 4*f2 + 3*f3)
            mau_so = 4 * (f1 - 2*f2 + f3)
            theta_opt = theta_B if abs(mau_so) < 1e-9 else tu_so / mau_so
                
            theta[n] = theta_opt
            v[n] = beta_fn(theta_opt, cfg) * np.exp(1j * theta_opt)
        if np.linalg.norm(v - v_old) < 1e-4: break
            
    return theta

def physics_inverse_solver(theta_target, cfg):
    N = len(theta_target)
    L1, L2, C = np.zeros(N), np.zeros(N), np.zeros(N)
    R = np.full(N, cfg.R_bounds[0]) 
    for n in range(N):
        target_phase = theta_target[n]
        target_amp = 0.99 
        
        def circuit_matching_loss(x):
            l1, l2, c = x[0], x[1], x[2]
            v_test = calculate_v_from_hardware(l1, l2, c, R[n], cfg)
            p_error = abs(np.angle(v_test) - target_phase)
            a_error = abs(np.abs(v_test) - target_amp)
            return p_error + 3.14 * a_error 
            
        x0 = [7e-9, 1.5e-9, 1.2e-12]
        res = minimize(circuit_matching_loss, x0, method='Nelder-Mead', options={'maxiter': 150})
        
        L1[n] = np.clip(res.x[0], cfg.L1_bounds[0], cfg.L1_bounds[1])
        L2[n] = np.clip(res.x[1], cfg.L2_bounds[0], cfg.L2_bounds[1])
        C[n]  = np.clip(res.x[2], cfg.C_bounds[0], cfg.C_bounds[1])
        
    return np.concatenate([L1, L2, C, R])

def optimize_IRS_Hardware_PSO_ThựcTế(hd, hr, G, cfg, theta_ao_guide):
    S, T, N = cfg.swarm_size, cfg.max_iter_PSO, cfg.N
    Phi = np.diag(hr.conj()) @ G
    hd_conj_T = hd.conj().T

    def fitness_hardware(flat_solution):
        L1 = flat_solution[0:N]
        L2 = flat_solution[N:2*N]
        C  = flat_solution[2*N:3*N]
        R  = flat_solution[3*N:4*N]
        v = calculate_v_from_hardware(L1, L2, C, R, cfg)
        channel_combined = v.conj().T @ Phi + hd_conj_T
        return np.log2(1 + (cfg.Pt / cfg.sigma2) * np.linalg.norm(channel_combined)**2)

    lb = np.concatenate([np.full(N, cfg.L1_bounds[0]), np.full(N, cfg.L2_bounds[0]), np.full(N, cfg.C_bounds[0]), np.full(N, cfg.R_bounds[0])])
    ub = np.concatenate([np.full(N, cfg.L1_bounds[1]), np.full(N, cfg.L2_bounds[1]), np.full(N, cfg.C_bounds[1]), np.full(N, cfg.R_bounds[1])])

    positions = np.random.uniform(lb, ub, (S, 4 * N))
    
    positions[0] = physics_inverse_solver(theta_ao_guide, cfg)
    positions[1] = np.clip(positions[0] + np.random.normal(0, 0.001, 4 * N) * (ub - lb), lb, ub)
    positions[2] = np.clip(positions[0] + np.random.normal(0, 0.003, 4 * N) * (ub - lb), lb, ub)
    
    velocities = np.zeros((S, 4 * N))
    v_max = (ub - lb) * 0.05 

    pbest_positions = np.copy(positions)
    pbest_scores = np.array([fitness_hardware(p) for p in positions])
    
    gbest_idx = np.argmax(pbest_scores)
    gbest_score = pbest_scores[gbest_idx]
    gbest_position = np.copy(positions[gbest_idx])

    for t in range(T):
        w = cfg.w_max - (cfg.w_max - cfg.w_min) * (t / T)
        r1, r2 = np.random.rand(S, 4 * N), np.random.rand(S, 4 * N)
        
        velocities = w * velocities + cfg.c1 * r1 * (pbest_positions - positions) + cfg.c2 * r2 * (gbest_position - positions)
        velocities = np.clip(velocities, -v_max, v_max)
        positions = np.clip(positions + velocities, lb, ub)

        for i in range(S):
            score = fitness_hardware(positions[i])
            if score > pbest_scores[i]:
                pbest_scores[i] = score
                pbest_positions[i] = np.copy(positions[i])
                if score > gbest_score:
                    gbest_score = score
                    gbest_position = np.copy(positions[i])

    top_5_idx = np.argsort(pbest_scores)[-5:]
    best_overall_score = gbest_score
    for idx in top_5_idx:
        local_sol = np.copy(pbest_positions[idx])
        for _ in range(50): 
            perturbation = np.random.normal(0, 0.001, 4 * N) * (ub - lb)
            candidate_sol = np.clip(local_sol + perturbation, lb, ub)
            c_score = fitness_hardware(candidate_sol)
            if c_score > best_overall_score:
                best_overall_score = c_score
                    
    return best_overall_score

if __name__ == "__main__":
    cfg = SystemHardwareConfig()
    d_array = np.arange(470, 505, 5)
    
    rates_Ideal, rates_AO, rates_hardware_PSO, rates_no_IRS = [], [], [], []
    print("Khởi chạy hệ thống tối ưu hóa RLC ...")

    for d in d_array:
        r_ideal, r_ao, r_pso, r_no = 0, 0, 0, 0
        pl_AP_user = path_loss(np.sqrt(d**2 + 2**2), cfg.alpha_AP_user, cfg.C0)
        pl_IRS_user = path_loss(np.sqrt((500 - d)**2 + 2**2), cfg.alpha_IRS_user, cfg.C0)
        pl_AP_IRS = path_loss(500.0, cfg.alpha_AP_IRS, cfg.C0)
        
        for _ in range(cfg.num_monte_carlo):
            hd = np.sqrt(pl_AP_user/2) * (np.random.randn(cfg.M) + 1j*np.random.randn(cfg.M))
            hr = np.sqrt(pl_IRS_user/2) * (np.random.randn(cfg.N) + 1j*np.random.randn(cfg.N))
            G = np.sqrt(pl_AP_IRS/2) * (np.random.randn(cfg.N, cfg.M) + 1j*np.random.randn(cfg.N, cfg.M))
            
            v_ideal = optimize_IRS_Ideal_AO(hd, hr, G, cfg)
            r_ideal += np.log2(1 + (cfg.Pt / cfg.sigma2) * np.linalg.norm(v_ideal.conj().T @ (np.diag(hr.conj()) @ G) + hd.conj().T)**2)
            
            theta_ao_guide = optimize_IRS_AO_Gốc(hd, hr, G, cfg)
            v_ao_temp = np.array([beta_fn(t, cfg) * np.exp(1j * t) for t in theta_ao_guide])
            r_ao += np.log2(1 + (cfg.Pt / cfg.sigma2) * np.linalg.norm(v_ao_temp.conj().T @ (np.diag(hr.conj()) @ G) + hd.conj().T)**2)
            
            r_pso += optimize_IRS_Hardware_PSO_ThựcTế(hd, hr, G, cfg, theta_ao_guide)
            
            r_no += np.log2(1 + (cfg.Pt / cfg.sigma2) * np.linalg.norm(hd)**2)
            
        rates_Ideal.append(r_ideal / cfg.num_monte_carlo)
        rates_AO.append(r_ao / cfg.num_monte_carlo)
        rates_hardware_PSO.append(r_pso / cfg.num_monte_carlo)
        rates_no_IRS.append(r_no / cfg.num_monte_carlo)
        print(f"Khoảng cách d={d}m | Ideal: {rates_Ideal[-1]:.3f} | Phần cứng RLC (PSO): {rates_hardware_PSO[-1]:.3f} | AO Bài báo: {rates_AO[-1]:.3f}")

    plt.figure(figsize=(11, 7))
    plt.plot(d_array, rates_hardware_PSO, marker='^', linestyle='-', color='red', linewidth=2.8, label='Practical IRS (Hardware PSO tối ưu mạch RLC )')
    plt.plot(d_array, rates_Ideal, marker='*', linestyle='-', color='purple', linewidth=2.2, label='Ideal IRS ')
    plt.plot(d_array, rates_AO, marker='o', linestyle='-', color='blue', linewidth=2.0, label='Practical IRS (AO gốc)')
    plt.plot(d_array, rates_no_IRS, marker='s', linestyle='--', color='black', linewidth=1.8, label='No IRS (Lower Bound Baseline)')
    
    plt.xlabel('AP-user horizontal distance: d (m)', fontsize=12, fontweight='bold')
    plt.ylabel('Achievable rate (bits/s/Hz)', fontsize=12, fontweight='bold')
    plt.title('ĐỒ THỊ HIỆU NĂNG VƯỢT TRỘI CỦA TỐI ƯU TRỰC TIẾP PHẦN CỨNG RLC VIA PSO', fontsize=12, fontweight='bold')
    plt.xticks(d_array)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11, loc='upper left')
    plt.tight_layout()
    plt.show()