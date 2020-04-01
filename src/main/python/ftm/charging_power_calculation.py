import numpy as np
import matplotlib.pyplot as plt


def calc_avg_charging_power_numeric(start_energy_in_J, batteryCapacityInJoule, maxChargingPowerInKw, chargingLimit,
                                    stepSize, return_plot_values=False):
    updatedEnergyLevelInJoule = start_energy_in_J
    currentTimestep = 1
    if return_plot_values:
        xvals = np.array([currentTimestep])
        yvals = np.array([updatedEnergyLevelInJoule])
    while (updatedEnergyLevelInJoule < chargingLimit):
        currentChargingPowerInKw = (0.6 * 0.05 ** (
                updatedEnergyLevelInJoule / batteryCapacityInJoule) + 0.4) * maxChargingPowerInKw
        stepEnergyInJoule = stepSize * currentChargingPowerInKw * 1000
        currentTimestep += stepSize
        updatedEnergyLevelInJoule += stepEnergyInJoule
        if return_plot_values:
            xvals = np.append(xvals, [currentTimestep])
            yvals = np.append(yvals, [updatedEnergyLevelInJoule])

    avgChargingPowerInKw = (chargingLimit - start_energy_in_J) / currentTimestep / 1000
    if return_plot_values:
        return (avgChargingPowerInKw, xvals, yvals)
    else:
        return avgChargingPowerInKw


def plot_charging_power_over_energy(e_max_in_j, p_max_in_kw):
    E_vals = np.linspace(0, e_max_in_j)
    xvals = E_vals / 3.6e6
    yvals = (0.6 * 0.05 ** (E_vals / e_max_in_j) + 0.4) * p_max_in_kw

    fig, ax = plt.subplots()
    ax.plot(xvals, yvals)
    ax.set_xlabel('SOC in kWh')
    ax.set_ylabel('Ladeleistung in kW')
    ax.set_ylim(0, yvals.max())
    ax.set_title('Ladeleistung in Abhängigkeit des Batterieladezustands')
    ax.grid()
    plt.show()


"""
E_max_in_J = 2.7e8
P_max_in_kW = 7.3
# Plot difference between linear and nonlinear charging
currentEnergyLevelInJoule = 2.608425116068747E8
currentEnergyLevelInJoule = 0.608425116068747E8
batteryCapacityInJoule = 2.699999827E8
chargingLimit = batteryCapacityInJoule
maxChargingPowerInKw = 7.2
stepSize = 100
fig, ax = plt.subplots()

(avgChargingPowerInKw, xvals, yvals) = calc_avg_charging_power_numeric(currentEnergyLevelInJoule, batteryCapacityInJoule, maxChargingPowerInKw, chargingLimit, stepSize)
sessionLengthInS = (chargingLimit - currentEnergyLevelInJoule) / 3.6e6 / avgChargingPowerInKw * 3600.0
print(sessionLengthInS)
ax.plot(xvals/3600, yvals/3.6e6, label='NonLinear: Stepsize '+str(stepSize))
ax.plot([0, sessionLengthInS/3600], [currentEnergyLevelInJoule/3.6e6, chargingLimit/3.6e6], label='NonLinear avg: Stepsize '+str(stepSize))

smallStepSize = 1
(avgChargingPowerInKwSmallStep, xvals, yvals) = calc_avg_charging_power_numeric(currentEnergyLevelInJoule, batteryCapacityInJoule, maxChargingPowerInKw, chargingLimit, smallStepSize)
sessionLengthInSSmallStep = (chargingLimit - currentEnergyLevelInJoule) / 3.6e6 / avgChargingPowerInKwSmallStep * 3600.0
ax.plot(xvals/3600, yvals/3.6e6, label='NonLinear: Stepsize '+str(smallStepSize))
ax.plot([0, sessionLengthInSSmallStep/3600], [currentEnergyLevelInJoule/3.6e6, chargingLimit/3.6e6], label='NonLinear avg: Stepsize '+str(smallStepSize))
print("Charging power stepsize ", stepSize, ":", avgChargingPowerInKw, ", stepSize ", smallStepSize, ":", avgChargingPowerInKwSmallStep, "Difference: ", avgChargingPowerInKw - avgChargingPowerInKwSmallStep, "Time diff:", sessionLengthInS -sessionLengthInSSmallStep)

# Linear soc dep
chargingPower = (0.6 * 0.05**(currentEnergyLevelInJoule / batteryCapacityInJoule) + 0.4) * maxChargingPowerInKw
sessionLengthInS = (chargingLimit - currentEnergyLevelInJoule) / 3.6e6 / chargingPower * 3600.0
ax.plot([0, sessionLengthInS/3600], [currentEnergyLevelInJoule/3.6e6, chargingLimit/3.6e6], label='Linear SOC dependent')

# Linear
chargingPower = maxChargingPowerInKw
sessionLengthInS = (chargingLimit - currentEnergyLevelInJoule) / 3.6e6 / chargingPower * 3600.0
ax.plot([0, sessionLengthInS/3600], [currentEnergyLevelInJoule/3.6e6, chargingLimit/3.6e6], label='Linear SOC independent')

ax.set_title('SOC during charging for different levels of detail')
ax.set_xlabel('Charging duration in h')
ax.set_ylabel('SOC in kWh')
ax.legend()
plt.show()
"""