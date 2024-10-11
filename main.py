import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


# Function for linear fit
def linear(x, k):
    return k * x


# Read data from the file
with open("dados.txt", "r") as f:
    lines = f.readlines()

# Remove any empty lines and strip whitespace
lines = [line.strip() for line in lines if line.strip() != ""]

# Split each line by tab and convert to float
data = [line.split("\t") for line in lines]
data = [[float(value) for value in line if value != ""] for line in data]

# Convert to a numpy array
data = np.array(data)

# Transpose the data so that each column corresponds to a displacement
forces_per_displacement = data.T.tolist()

# Number of displacements and number of measurements per displacement
N_disp = len(forces_per_displacement)
M = len(
    forces_per_displacement[0]
)  # Assuming all columns have the same number of measurements

# Generate list of displacements
delta_x_cm = 0.05  # Instrument error in cm

desloc_inicial = float(input("Digite o deslocamento inicial (em cm): "))
incremento_disp = float(input("Digite o incremento de deslocamento (em cm): "))

# Generate displacement values
deslocamentos = [desloc_inicial + i * incremento_disp for i in range(N_disp)]

# Instrumental uncertainty (resolution of the force sensor)
instrument_uncertainty = (
    0.0125  # Replace with your instrument's resolution if different
)

# Calculate mean and uncertainty for each displacement
media_forcas = []
incertezas_forca = []

for forces in forces_per_displacement:
    media = np.mean(forces)
    desvio_padrao = np.std(forces, ddof=1)  # Sample standard deviation
    incerteza = desvio_padrao / np.sqrt(len(forces))  # Standard error of the mean

    # If the calculated uncertainty is zero, use the instrumental uncertainty
    if incerteza == 0:
        incerteza = instrument_uncertainty / np.sqrt(len(forces))

    media_forcas.append(media)
    incertezas_forca.append(incerteza)

# Convert displacements to meters
deslocamentos_m = np.array(deslocamentos) / 100  # cm to m
delta_x = delta_x_cm / 100  # Convert error to meters

# Linear fit to determine k
popt, pcov = curve_fit(
    linear, deslocamentos_m, media_forcas, sigma=incertezas_forca, absolute_sigma=True
)
k = popt[0]
dk = np.sqrt(np.diag(pcov))[0]

print(f"\nConstante de mola k = {k:.4f} N/m ± {dk:.4f} N/m")

# Propagate the error from displacement to force using f = kx
df_x = k * delta_x

# Combine uncertainties (uncertainty of force and uncertainty due to x)
incertezas_totais = np.sqrt(np.array(incertezas_forca) ** 2 + df_x**2)

# Generate LaTeX table entries
entradas_tabela = []

for i in range(N_disp):
    x = deslocamentos[i]
    dx = delta_x_cm  # Error in cm
    f_media = media_forcas[i]
    df_total = incertezas_totais[i]
    entrada = (x, dx, f_media, df_total)
    entradas_tabela.append(entrada)

# Generate LaTeX code for the table

codigo_latex = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage[brazil]{babel}
\usepackage{siunitx}
\sisetup{
  locale = DE, % Define a vírgula como separador decimal
  per-mode=symbol,
  output-decimal-marker={,}
}
\begin{document}

\begin{table}[h]
\centering
\begin{tabular}{c c}
\hline
\textbf{Deslocamento (cm)} & \textbf{Força (N)} \\
\hline
"""

for entrada in entradas_tabela:
    x = entrada[0]
    dx = entrada[1]
    f_media = entrada[2]
    df = entrada[3]
    x_str = r"$\SI{{{:.2f} \pm {:.2f}}}{{\centi\meter}}$".format(x, dx)
    f_str = r"$\SI{{{:.4f} \pm {:.4f}}}{{\newton}}$".format(f_media, df)
    codigo_latex += f"{x_str} & {f_str} \\\\\n"

codigo_latex += r"""\hline
\end{tabular}
\caption{Medições de força em função do deslocamento.}
\label{tab:forca_deslocamento}
\end{table}

\end{document}
"""


with open("tabela.tex", "w") as f:
    f.write(codigo_latex)

# Plot force vs. displacement with linear fit
plt.figure(figsize=(8, 6))
plt.errorbar(
    deslocamentos_m,
    media_forcas,
    xerr=delta_x,
    yerr=incertezas_totais,
    fmt="o",
    label="Dados experimentais",
)
x_fit = np.linspace(min(deslocamentos_m), max(deslocamentos_m), 100)
plt.plot(
    x_fit, linear(x_fit, *popt), label=f"Ajuste linear: $f = ({k:.2f} \\pm {dk:.2f})x$"
)
plt.xlabel("Deslocamento (m)")
plt.ylabel("Força (N)")
plt.title("Gráfico de Força vs Deslocamento")
plt.legend()
plt.grid(True)
plt.savefig("grafico.png")

# Plot residuals
plt.figure(figsize=(8, 6))
residuos = media_forcas - linear(deslocamentos_m, *popt)
plt.errorbar(deslocamentos_m, residuos, yerr=incertezas_totais, fmt="o")
plt.hlines(
    0, min(deslocamentos_m), max(deslocamentos_m), colors="r", linestyles="dashed"
)
plt.xlabel("Deslocamento (m)")
plt.ylabel("Resíduo (N)")
plt.title("Gráfico dos Resíduos")
plt.grid(True)
plt.savefig("residuos.png")
