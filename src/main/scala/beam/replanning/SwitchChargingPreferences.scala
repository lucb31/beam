package beam.replanning

import javax.inject.Inject
import org.matsim.api.core.v01.population.{Activity, HasPlansAndId, Leg, Person, Plan}
import org.matsim.core.config.Config
import org.slf4j.LoggerFactory

class SwitchChargingPreferences @Inject()(config: Config) extends PlansStrategyAdopter {
  private val log = LoggerFactory.getLogger(classOf[SwitchChargingPreferences])

  override def run(person: HasPlansAndId[Plan, Person]): Unit = {
    log.debug("Before Replanning SwitchChargingPreferences: Person-" + person.getId + " - " + person.getPlans.size())
    var previousChargeSelection = 0
    if (person.getSelectedPlan.getAttributes.getAttribute("chargeAtActivity") != null)
      previousChargeSelection = person.getSelectedPlan.getAttributes.getAttribute("chargeAtActivity").asInstanceOf[Int]
    ReplanningUtil.makeExperiencedMobSimCompatible(person)
    ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)

    person.getSelectedPlan.getAttributes.clear()  // ! May cause some problems
    person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", previousChargeSelection + 1)
    log.debug("After Replanning ClearModes: Person-" + person.getId + " - " + person.getPlans.size())
  }
}
