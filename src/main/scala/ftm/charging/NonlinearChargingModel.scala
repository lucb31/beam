package ftm.charging

object NonlinearChargingModel {
  def calcChargingPower(currentEnergyLevelInJoule: Double, batteryCapacityInJoule: Double, maxChargingPowerInKw: Double): Double = {
    (0.6 * Math.pow(0.05, currentEnergyLevelInJoule / batteryCapacityInJoule) + 0.4) * maxChargingPowerInKw
  }

  def calcAvgChargingPowerNumeric(currentEnergyLevelInJoule: Double, batteryCapacityInJoule: Double, maxChargingPowerInKw: Double, chargingLimits: (Double, Double)): Double = {
    var updatedEnergyLevelInJoule = currentEnergyLevelInJoule
    var currentTimestep = 1 // Start at 1 to avoid division by zero
    val stepSize = 10 // TODO Make this a config value
    while(updatedEnergyLevelInJoule < chargingLimits._2) {
      val currentChargingPowerInKw = NonlinearChargingModel.calcChargingPower(currentEnergyLevelInJoule, batteryCapacityInJoule, maxChargingPowerInKw)
      val stepEnergyInJoule = stepSize * currentChargingPowerInKw * 1000 // 3.6e6 / 3600 = 1000
      currentTimestep += stepSize
      updatedEnergyLevelInJoule += stepEnergyInJoule
    }
    (chargingLimits._2 - currentEnergyLevelInJoule) / currentTimestep / 1000
  }

}
