import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt

torch.manual_seed(42)
np.random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class PINN(nn.Module):
    def __init__(self, layers):
        super(PINN, self).__init__()
        self.hidden_layers = nn.ModuleList()
        for i in range(len(layers) - 2):
            self.hidden_layers.append(nn.Linear(layers[i], layers[i+1]))
        self.output_layer = nn.Linear(layers[-2], layers[-1])
        self.activation = nn.Tanh()
    
    def forward(self, t, x):
        inputs = torch.cat([t, x], dim=1)
        for layer in self.hidden_layers:
            inputs = self.activation(layer(inputs))
        u = self.output_layer(inputs)
        return u

def pde_residual(model, t, x, visc):
    t.requires_grad_(True)
    x.requires_grad_(True)
    u = model(t, x)
    u_t = torch.autograd.grad(u, t, grad_outputs=torch.ones_like(u), create_graph = True)[0]
    u_x = torch.autograd.grad(u, x, grad_outputs=torch.ones_like(u), create_graph = True)[0]
    u_xx = torch.autograd.grad(u_x, x, grad_outputs=torch.ones_like(u_x), create_graph = True)[0]
    residual = u_t + u*u_x - visc*u_xx
    return residual

def data_gen(i_b_points, collocation_points):
    x_ic = np.random.uniform(-1, 1, (i_b_points//3, 1))
    t_ic = np.zeros_like(x_ic)
    u_ic = -np.sin(np.pi * x_ic)

    t_bc1 = np.random.uniform(0, 1, (i_b_points // 3, 1))
    x_bc1 = -np.ones_like(t_bc1)
    u_bc1 = np.zeros_like(t_bc1)

    t_bc2 = np.random.uniform(0, 1, (i_b_points - 2*(i_b_points // 3), 1))
    x_bc2 = np.ones_like(t_bc2)
    u_bc2 = np.zeros_like(t_bc2)

    t_u = np.vstack([t_ic, t_bc1, t_bc2])
    x_u = np.vstack([x_ic, x_bc1, x_bc2])
    u_u = np.vstack([u_ic, u_bc1, u_bc2])

    t_colloc = np.random.uniform(0, 1, (collocation_points, 1))
    x_colloc = np.random.uniform(-1, 1, (collocation_points, 1))

    t_u = torch.tensor(t_u, dtype=torch.float32)
    x_u = torch.tensor(x_u, dtype=torch.float32)
    u_u = torch.tensor(u_u, dtype=torch.float32)
    t_colloc = torch.tensor(t_colloc, dtype=torch.float32)
    x_colloc = torch.tensor(x_colloc, dtype=torch.float32)

    return t_u, x_u, u_u, t_colloc, x_colloc

layers = [2, 20, 20, 20, 20, 20, 20, 20, 20, 1]
visc = 0.01/np.pi
epochs = 10001
learning_rate = 1e-4
print(f"Training on: {device}")
model = PINN(layers).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
t_u, x_u, u_u, t_f, x_f = data_gen(i_b_points=100, collocation_points=10000)
t_u = t_u.to(device)
x_u = x_u.to(device)
u_u = u_u.to(device)
t_f = t_f.to(device)
x_f = x_f.to(device)
mse = nn.MSELoss()

print("Starting training")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Training on: {device}")
for epoch in range(epochs):
    optimizer.zero_grad()
    u_pred = model(t_u, x_u)
    loss_u = mse(u_pred, u_u)
    f_pred = pde_residual(model, t_f, x_f, visc)
    loss_f = mse(f_pred, torch.zeros_like(f_pred))
    total_loss = loss_u + loss_f
    total_loss.backward()
    optimizer.step()
    if epoch%500 == 0 and epoch != 0:
        print("Epoch: {}".format(epoch))
        print("Total loss: {}".format(total_loss))

def plot_results(model, device):
    # 1. Create a dense grid of t and x points
    t_flat = np.linspace(0, 1, 100)
    x_flat = np.linspace(-1, 1, 256)
    T, X = np.meshgrid(t_flat, x_flat)
    
    # Flatten the grid for the neural network
    t_tensor = torch.tensor(T.flatten()[:, None], dtype=torch.float32).to(device)
    x_tensor = torch.tensor(X.flatten()[:, None], dtype=torch.float32).to(device)
    
    # 2. Predict u(t, x) using the trained model
    model.eval() # Set model to evaluation mode
    with torch.no_grad(): # We don't need gradients for plotting
        u_pred = model(t_tensor, x_tensor)
        
    # Reshape the 1D predictions back into the 2D grid shape
    U_pred = u_pred.cpu().numpy().reshape(X.shape)
    
    # 3. Plot the heatmap
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # contourf creates a filled contour plot (heatmap)
    cmap = ax.contourf(T, X, U_pred, levels=100, cmap='jet')
    fig.colorbar(cmap, label='Velocity (u)')
    
    ax.set_title("PINN Solution for Burger's Equation")
    ax.set_xlabel("Time (t)")
    ax.set_ylabel("Space (x)")
    
    plt.show()

plot_results(model, device)