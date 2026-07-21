import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt

# -----------------------------
# Problem setup: u_t = alpha u_xx
# Domain: x in [0,1], t in [0,1]
# BC: u(0,t)=u(1,t)=0
# IC: u(x,0)=sin(pi x)
# -----------------------------
alpha = 0.1

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
torch.manual_seed(0)

class MLP(nn.Module):
    def __init__(self, in_dim=2, out_dim=1, width=64, depth=4):
        super().__init__()
        layers = [nn.Linear(in_dim, width), nn.Tanh()]
        for _ in range(depth - 1):
            layers += [nn.Linear(width, width), nn.Tanh()]
        layers += [nn.Linear(width, out_dim)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

model = MLP(width=64, depth=4).to(device)

def exact_solution(x, t):
    # u(x,t)=exp(-alpha*pi^2*t)*sin(pi*x)
    return torch.exp(-alpha * (np.pi**2) * t) * torch.sin(np.pi * x)

# ---------- Sampling ----------
def sample_interior(Nf):
    x = torch.rand(Nf, 1, device=device)
    t = torch.rand(Nf, 1, device=device)
    return x, t

def sample_boundary(Nb):
    t = torch.rand(Nb, 1, device=device)
    x0 = torch.zeros(Nb, 1, device=device)
    x1 = torch.zeros(Nb, 1, device=device)
    return (x0, t), (x1, t)

def sample_initial(N0):
    x = torch.rand(N0, 1, device=device)
    t = torch.zeros(N0, 1, device=device)
    x0 = 0.5

    sigma = 0.05
    u0 = torch.exp(-((x - 0.5)**2) / (2 * sigma**2))
    return x, t, u0

# ---------- PINN residual ----------
def pde_residual(x, t):
    x = x.requires_grad_(True)
    t = t.requires_grad_(True)

    xt = torch.cat([x, t], dim=1)
    u = model(xt)

    u_t = torch.autograd.grad(u, t, torch.ones_like(u), create_graph=True)[0]
    u_x = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, x, torch.ones_like(u_x), create_graph=True)[0]

    return u_t - alpha * u_x

# ---------- Training ----------
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

# weights for loss terms (often helps)
w_pde = 1.0
w_bc  = 10.0
w_ic  = 10.0

Nf, Nb, N0 = 2000, 200, 200
steps = 5000

for step in range(1, steps + 1):
    optimizer.zero_grad()

    # PDE loss
    x_f, t_f = sample_interior(Nf)
    r = pde_residual(x_f, t_f)
    loss_pde = (r**2).mean()

    # BC loss
    (x0, tb), (x1, tb2) = sample_boundary(Nb)
    u0b = model(torch.cat([x0, tb], dim=1))
    u1b = model(torch.cat([x1, tb2], dim=1))
    loss_bc = ((u0b-1)**2).mean() + (u1b**2).mean()

    # IC loss
    x0i, t0i, u0_true = sample_initial(N0)
    u0_pred = model(torch.cat([x0i, t0i], dim=1))
    loss_ic = ((u0_pred - u0_true)**2).mean()

    loss = w_pde * loss_pde + w_bc * loss_bc + w_ic * loss_ic
    loss.backward()
    optimizer.step()

    if step % 500 == 0:
        print(f"step {step:5d} | loss {loss.item():.3e} | pde {loss_pde.item():.3e} | bc {loss_bc.item():.3e} | ic {loss_ic.item():.3e}")

# ---------- Evaluate / Plot ----------
model.eval()
with torch.no_grad():
    # grid
    nx, nt = 200, 200
    x = torch.linspace(0, 1, nx, device=device).reshape(-1, 1)
    t = torch.linspace(0, 1, nt, device=device).reshape(-1, 1)
    X, T = torch.meshgrid(x.squeeze(1), t.squeeze(1), indexing="ij")
    xt = torch.stack([X.reshape(-1), T.reshape(-1)], dim=1)
    u_pred = model(xt).reshape(nx, nt)

    u_ex = exact_solution(X, T)

    rel_l2 = torch.linalg.norm(u_pred - u_ex) / torch.linalg.norm(u_ex)
    print("Relative L2 error:", rel_l2.item())

    # plot at a few time slices
    plt.figure()
    for tt in [0.0, 0.25, 0.5, 1.0]:
        tidx = int(tt * (nt - 1))
        plt.plot(x.cpu().numpy(), u_pred[:, tidx].cpu().numpy(), label=f"PINN t={tt}")
        #plt.plot(x.cpu().numpy(), u_ex[:, tidx].cpu().numpy(), "--", label=f"Exact t={tt}")
    plt.xlabel("x")
    plt.ylabel("u(x,t)")
    plt.legend()
    plt.tight_layout()
    plt.show()
