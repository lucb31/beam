package ftm.run

import com.typesafe.scalalogging.StrictLogging
import ftm.util.PopulationUtil

import scala.language.postfixOps
import scala.util.Random

object DebugPlayground extends App with StrictLogging {
  logger.info("Hello")
  print("Hello world")


  val numberOfActivities = 5
  val numberOfCombinations = Math.pow(2, numberOfActivities-1).toInt
  for (chargeAtActivity <- 0 to numberOfCombinations) {
    val sequence = (numberOfCombinations + chargeAtActivity).toBinaryString.tail.map{ case '1' => true; case _ => false }.reverse
    val newSeq = PopulationUtil.addChargingActivityToChargingSequence(sequence)
    val removedSeq = PopulationUtil.removeChargingActivityFromChargingSequence(newSeq)
    val movedSeq = PopulationUtil.moveChargingActivityInChargingSequence(sequence)
    val indexMovedSeq = PopulationUtil.moveChargingActivityToNextOpenSlotInChargingSequence(sequence, 2)
    val debugg = 0
  }

  val minSoc = 0.4
  // Calculate probabilities
  val PMoveChargingActivity = 0.2
  var PAddChargingActivity = 0.2
  var PRemoveChargingActivity = 0.6
  if (minSoc < 0.5) {
    PAddChargingActivity = 0.6
    PRemoveChargingActivity = 0.2
  }

  // Decide what to do
  var added = 0
  var removed = 0
  var moved = 0
  for (i <- 0 to 100) {
    val selection = Random.nextDouble()
    if (selection < PRemoveChargingActivity) {
      removed += 1
    } else if (selection < PRemoveChargingActivity + PAddChargingActivity) {
      added += 1
    } else {
      moved += 1
    }
  }
  print("added: ", added, "removed:", removed, "moved", moved)

}
