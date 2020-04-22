package ftm.util

import beam.replanning.ReplanningUtil
import org.matsim.api.core.v01.network.Link
import org.matsim.api.core.v01.{Coord, Id}
import org.matsim.api.core.v01.population.{Activity, HasPlansAndId, Leg, Person, Plan, Route}
import org.matsim.facilities.ActivityFacility
import org.matsim.utils.objectattributes.attributable.Attributes

import scala.collection.mutable.ArrayBuffer
import scala.util.Random

object PopulationUtil {
  def copyPlanAndSelectRandomChargingPreference(person: HasPlansAndId[Plan, Person]): Unit = {
    // Determine number of different combinations by number of activities
    val activities = getNumberOfActivities(person.getSelectedPlan)
    val numberOfCombinations = Math.pow(2, activities-1).toInt

    // Select random combination of charging preference
    val random = new Random()
    val chargeAtActivity = random.nextInt(numberOfCombinations + 1)
    //ReplanningUtil.makeExperiencedMobSimCompatible(person)
    ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)
    person.getSelectedPlan.getAttributes.removeAttribute("chargeAtActivity")
    person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", chargeAtActivity)
  }

  def getNumberOfActivities(plan: Plan): Int = {
    var activities = 0
    plan.getPlanElements.forEach {
      case a: Activity => if (a.getType != "Dummy") activities += 1
      case _ =>
    }
    activities
  }
  def getChargeAtActivityBooleanSeq(plan: Plan): IndexedSeq[Boolean] = {
    //val combinations = scala.math.pow(2, matsimPlan.getPlanElements.size() - 1).toInt
    val numberOfCombinations = Math.pow(2, getNumberOfActivities(plan)-1).toInt
    val chargeAtActivity = plan.getAttributes.getAttribute("chargeAtActivity").asInstanceOf[Int]
    (numberOfCombinations + chargeAtActivity).toBinaryString.tail.map{ case '1' => true; case _ => false }.reverse
  }

  def chargeAtActivityBooleanSeqToString(booleanSeq: IndexedSeq[Boolean]): Int = {
    var sum = 0.0
    booleanSeq.zipWithIndex.foreach {
      case (value, index) => {
        if (value)
          sum += math.pow(2, index.toInt)
      }
      case _ =>
    }
    sum.toInt
  }

  def addChargingActivityToChargingSequence(sequence: IndexedSeq[Boolean]): IndexedSeq[Boolean] = {
    // Check if we are already charging at every activity
    var newSequence = sequence
    if (sequence.filter(value => value).size < sequence.size) {
      var change = false
      while (!change) {
        val randomIndex = Random.nextInt(sequence.length)
        if (!sequence(randomIndex)) {
          newSequence = sequence.updated(randomIndex, true)
          change = true
        }
      }
    }
    newSequence
  }

  def removeChargingActivityFromChargingSequence(sequence: IndexedSeq[Boolean]): IndexedSeq[Boolean] = {
    // Check if we have a charging activity to remove
    var newSequence = sequence
    if (sequence.filter(value => value).size > 0) {
      var change = false
      while (!change) {
        val randomIndex = Random.nextInt(sequence.length)
        if (sequence(randomIndex)) {
          newSequence = sequence.updated(randomIndex, false)
          change = true
        }
      }
    }
    newSequence
  }

  def moveChargingActivityInChargingSequence(sequence: IndexedSeq[Boolean]): IndexedSeq[Boolean] = {
    // Removes a random charging activity from the sequence and adds a new one at a random position
    // Sequence cannot stay the same

    // Check if we have a charging activity to move
    var newSequence = sequence
    if (sequence.filter(value => value).size > 0) {
      // make sure the sequence has changed
      while(newSequence == sequence) {
        newSequence = removeChargingActivityFromChargingSequence(newSequence)
        newSequence = addChargingActivityToChargingSequence(newSequence)
      }
    }
    newSequence
  }

  def moveChargingActivityToNextOpenSlotInChargingSequence(sequence: IndexedSeq[Boolean], index: Int): IndexedSeq[Boolean] = {
    // Moves specific charging activity to the next possible time
    var newSequence = sequence
    // Check if there is a charging activity at index position
    if (sequence(index)) {
      var success = false
      for (nextIndex <- index+1 to sequence.size - 1) {
        if (!success && !sequence(nextIndex)) {
          newSequence = sequence.updated(nextIndex, true)
          newSequence = newSequence.updated(index, false)
          success = true
        }
      }
    }
    newSequence
  }

  def repeatPersonPlan(plan: Plan, iterations: Int, maxHour: Int): Plan = {
    val activities: ArrayBuffer[Activity] = new ArrayBuffer()
    val legs: ArrayBuffer[Leg] = new ArrayBuffer()
    plan.getPlanElements.forEach {
      case activity: Activity => activities += activity
      case leg: Leg => legs += leg
    }
    val lastActivity = activities(activities.size - 1)
    /*
     */
    if (activities(0).getCoord.equals(lastActivity.getCoord)) {
      plan.getPlanElements.remove(lastActivity)
      activities.remove(activities.size - 1)
    }
    else {
      if (lastActivity.getEndTime < 0)
        lastActivity.setEndTime(maxHour*3600)
      val toHomeLeg = cloneLeg(legs(0))
      toHomeLeg.setDepartureTime(lastActivity.getEndTime)
      legs += toHomeLeg
      plan.addLeg(toHomeLeg)
    }

    for (iteration <- 1 to iterations) {
      for (index <- 0 to activities.size - 1) {
        val activity = cloneActivity(activities(index))
        activity.setEndTime(activity.getEndTime + iteration*maxHour*3600)
        plan.addActivity(activity)

        if (index < legs.size) {
          val leg = cloneLeg(legs(index))
          leg.setDepartureTime(leg.getDepartureTime + iteration*maxHour*3600)
          plan.addLeg(leg)
        }
      }
    }
    if (activities(0).getCoord.equals(lastActivity.getCoord))
      plan.addActivity(lastActivity)
    else
      plan.getPlanElements.remove(plan.getPlanElements.size() - 1)

    plan
  }

  def getActivitiesFromPlan(plan: Plan): ArrayBuffer[Activity] = {
    val activities: ArrayBuffer[Activity] = new ArrayBuffer()
    plan.getPlanElements.forEach {
      case activity: Activity =>
        // Ignore dummy activities
        if (activity.getType != "Dummy")  activities += activity
      case _ =>
    }
    activities
  }
/*
  def getActivitiesAndLegsFromPlan(plan: Plan): ArrayBuffer[Activity] = {
    val activities: ArrayBuffer[Activity] = new ArrayBuffer()
    plan.getPlanElements.forEach {
      case activity: Activity => activities += activity
    }
    activities
  }


 */
  def cloneActivity(activity: Activity): Activity = {
    new Activity {
      var endTime: Double = activity.getEndTime
      var startTime: Double = activity.getStartTime
      var activityType: String = activity.getType
      var activityLocation: Coord = activity.getCoord
      var maxDuration: Double = activity.getStartTime
      var linkId = activity.getLinkId
      var facilityId = activity.getFacilityId
      var attributes = activity.getAttributes
      override def getEndTime: Double = endTime
      override def setEndTime(seconds: Double): Unit = endTime = seconds
      override def getType: String = activityType
      override def setType(`type`: String): Unit = activityType = `type`
      override def getCoord: Coord = activityLocation
      override def getStartTime: Double = startTime
      override def setStartTime(seconds: Double): Unit = startTime = seconds
      override def getMaximumDuration: Double = maxDuration
      override def setMaximumDuration(seconds: Double): Unit = maxDuration = seconds
      override def getLinkId: Id[Link] = linkId
      override def getFacilityId: Id[ActivityFacility] = facilityId
      override def setLinkId(id: Id[Link]): Unit = linkId = id
      override def setFacilityId(id: Id[ActivityFacility]): Unit = facilityId = id
      override def setCoord(coord: Coord): Unit = activityLocation = coord
      override def getAttributes: Attributes = attributes
    }
  }
  
  def cloneLeg(leg: Leg): Leg = {
    new Leg {
      var mode: String = leg.getMode
      var route: Route = leg.getRoute
      var departureTime: Double = leg.getDepartureTime
      var travelTime: Double = leg.getTravelTime
      var attributes: Attributes = leg.getAttributes
      override def getMode: String = mode
      override def setMode(newMode: String): Unit = mode = newMode
      override def getRoute: Route = route
      override def setRoute(newRoute: Route): Unit = route = newRoute
      override def getDepartureTime: Double = departureTime
      override def setDepartureTime(seconds: Double): Unit = departureTime = seconds
      override def getTravelTime: Double = travelTime
      override def setTravelTime(seconds: Double): Unit = travelTime = seconds
      override def getAttributes: Attributes = attributes
    }
  }
}
