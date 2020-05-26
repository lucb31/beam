package ftm.charging

object NonlinearChargingModel {
  def calcChargingPower(currentEnergyLevelInJoule: Double, batteryCapacityInJoule: Double, maxChargingPowerInKw: Double): Double = {
    if (currentEnergyLevelInJoule > 0.0)
      (0.6 * Math.pow(0.05, currentEnergyLevelInJoule / batteryCapacityInJoule) + 0.4) * maxChargingPowerInKw
    else
      maxChargingPowerInKw
  }

  def calcAvgChargingPowerNumeric(currentEnergyLevelInJoule: Double, batteryCapacityInJoule: Double, maxChargingPowerInKw: Double, chargingLimits: (Double, Double), stepSize: Int = 10): Double = {
    var updatedEnergyLevelInJoule = currentEnergyLevelInJoule
    var currentTimestep = 1 // Start at 1 to avoid division by zero
    while(updatedEnergyLevelInJoule < chargingLimits._2) {
      val currentChargingPowerInKw = NonlinearChargingModel.calcChargingPower(updatedEnergyLevelInJoule, batteryCapacityInJoule, maxChargingPowerInKw)
      val stepEnergyInJoule = stepSize * currentChargingPowerInKw * 1000 // 3.6e6 / 3600 = 1000
      currentTimestep += stepSize
      updatedEnergyLevelInJoule += stepEnergyInJoule
    }
    (chargingLimits._2 - currentEnergyLevelInJoule) / currentTimestep / 1000
  }

}
