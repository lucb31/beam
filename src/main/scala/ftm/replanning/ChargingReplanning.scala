package ftm.replanning

import beam.agentsim.agents.parking.ChoosesParking
import beam.replanning.{PlansStrategyAdopter, ReplanningUtil}
import ftm.util.PopulationUtil
import javax.inject.Inject
import org.matsim.api.core.v01.population._
import org.matsim.core.config.Config
import org.slf4j.LoggerFactory

import scala.util.Random

class ChargingReplanning @Inject()(config: Config) extends PlansStrategyAdopter {
  private val log = LoggerFactory.getLogger(classOf[ChargingReplanning])

  override def run(person: HasPlansAndId[Plan, Person]): Unit = {
    log.debug("Before Replanning ChargingReplanning: Person-" + person.getId + " - " + person.getPlans.size())
    ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)
    val minSoc = person.getSelectedPlan.getAttributes.getAttribute("minSoc").asInstanceOf[Double]
    val chargingSequence = PopulationUtil.getChargeAtActivityBooleanSeq(person.getSelectedPlan)
    var newChargingSequence = chargingSequence

    // Calculate probabilities
    var PMoveChargingActivity = 0.2
    var PAddChargingActivity = 0.2
    var PRemoveChargingActivity = 0.6
    if (chargingSequence.filter(value => value).size == 0) {
      // No Charging planned
      PAddChargingActivity = 1.0
      PMoveChargingActivity = 0.0
      PRemoveChargingActivity = 0.0
    }
    else if(chargingSequence.filter(value => value).size == chargingSequence.size) {
      // Charging at every activity planned
      PAddChargingActivity = 0.0
      PMoveChargingActivity = 0.0
      PRemoveChargingActivity = 1.0
    }
    else if (minSoc < 0.5) {
      PAddChargingActivity = 0.6
      PRemoveChargingActivity = 0.2
    }

    // Decide what to do
    val selection = Random.nextDouble()
    if (selection < PRemoveChargingActivity) {
      newChargingSequence = PopulationUtil.removeChargingActivityFromChargingSequence(chargingSequence)
    } else if (selection < PRemoveChargingActivity + PAddChargingActivity) {
      newChargingSequence = PopulationUtil.addChargingActivityToChargingSequence(chargingSequence)
    } else {
      newChargingSequence = PopulationUtil.moveChargingActivityInChargingSequence(chargingSequence)
    }

    val newChargeAtActivity = PopulationUtil.chargeAtActivityBooleanSeqToString(newChargingSequence)
    person.getSelectedPlan.getAttributes.removeAttribute("chargeAtActivity")
    person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", newChargeAtActivity)

    log.debug("After Replanning ChargingReplanning: Person-" + person.getId + " - " + person.getPlans.size())
  }
}
