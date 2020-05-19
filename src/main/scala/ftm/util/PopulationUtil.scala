package ftm.util

import beam.replanning.ReplanningUtil
import org.matsim.api.core.v01.network.{Link, Network}
import org.matsim.api.core.v01.{Coord, Id}
import org.matsim.api.core.v01.population.{Activity, HasPlansAndId, Leg, Person, Plan, Population, Route}
import org.matsim.core.config.ConfigUtils
import org.matsim.core.network.NetworkUtils
import org.matsim.core.population.PopulationUtils
import org.matsim.facilities.ActivityFacility
import org.matsim.utils.objectattributes.attributable.Attributes

import scala.collection.mutable.ArrayBuffer
import scala.util.Random

object PopulationUtil {
  def generateSamplePopulation(samplePopulationSize: Int, inputPopulation: Population): Population = {
    generateSamplePopulation(samplePopulationSize, inputPopulation, 0.9)
  }

  def generateSamplePopulation(samplePopulationSize: Int, inputPopulation: Population, workActivityRatio: Double): Population = {
    val config = ConfigUtils.createConfig()
    var outputPopulation = PopulationUtils.createPopulation(config)
    // Validate workActivityRatio
    if (workActivityRatio > 1 || workActivityRatio < 0) {
      outputPopulation = inputPopulation
    }
    else if (samplePopulationSize > 0 && samplePopulationSize < inputPopulation.getPersons.size()) {
      val random: Random = new Random()
      var randomPersonArray = random.shuffle(inputPopulation.getPersons.values().toArray.toSeq)
      var personsWithoutWorkAct = 0
      while (outputPopulation.getPersons.size() < samplePopulationSize && randomPersonArray.size > 0) {
        val person = randomPersonArray(0).asInstanceOf[Person]
        if (!checkIfPersonHasWorkAct(person)) {
          if (personsWithoutWorkAct < (1 - workActivityRatio) * samplePopulationSize) {
            outputPopulation.addPerson(person)
            personsWithoutWorkAct += 1
          }
        }
        else {
          outputPopulation.addPerson(person)
        }
        randomPersonArray = randomPersonArray.drop(1)
      }
    }
    else
      outputPopulation = inputPopulation
    outputPopulation
  }

  def generateSamplePopulation(samplePopulationSize: Int, inputPopulation: Population, network: Network): Population = {
    generateSamplePopulation(samplePopulationSize, inputPopulation, network, 0.9)
  }

  def generateSamplePopulation(samplePopulationSize: Int, inputPopulation: Population, network: Network, workActivityRatio: Double): Population = {
    // Checks if persons in proximity to a network link
    val config = ConfigUtils.createConfig()
    var outputPopulation = PopulationUtils.createPopulation(config)
    if (workActivityRatio > 1 || workActivityRatio < 0) {
      outputPopulation = inputPopulation
    }
    else if (samplePopulationSize > 0 && samplePopulationSize < inputPopulation.getPersons.size()) {
      val random: Random = new Random()
      var randomPersonArray = random.shuffle(inputPopulation.getPersons.values().toArray.toSeq)
      var personsWithoutWorkAct = 0
      while (outputPopulation.getPersons.size() < samplePopulationSize && randomPersonArray.size > 0) {
        val person = randomPersonArray(0).asInstanceOf[Person]

        if (checkIfPersonWithinNetworkBoundaries(network, person)) {
          if (!checkIfPersonHasWorkAct(person)) {
            if (personsWithoutWorkAct < (1 - workActivityRatio) * samplePopulationSize) {
              outputPopulation.addPerson(person)
              personsWithoutWorkAct += 1
            }
          }
          else {
            outputPopulation.addPerson(person)
          }
        }
        randomPersonArray = randomPersonArray.drop(1)
      }
    }
    else
      outputPopulation = inputPopulation
    outputPopulation

  }


  def checkIfPersonHasWorkAct(person: Person): Boolean = {
    person.getSelectedPlan.getPlanElements.forEach({
      case activity: Activity =>
        if (activity.getType == "Work") {
          return true
        }
      case _ =>
    })
    false
  }
  def checkIfPersonWithinNetworkBoundaries(network: Network, person: Person, maxDistanceToNetwork: Double = 300.0, ignoreNighttimeActs: Boolean = true): Boolean = {
    // Check for activities within proximity to network nodes and across day boundaries / nighttime activities
    var prevActivityEndTime = 0.0
    var prevLegDepartureTime = 0.0
    person.getSelectedPlan.getPlanElements.forEach({
      case activity: Activity =>
        // Check for nighttime activity
        val activityEndTime = activity.getEndTime
        if (activityEndTime > 0.0 && activityEndTime < prevActivityEndTime) {
          if (ignoreNighttimeActs) return false
          activity.setEndTime(24 * 3600 + activityEndTime)
        }

        // Check if activity has a network node near it
        val distanceToNetwork = NetworkUtils.getEuclideanDistance(activity.getCoord, NetworkUtils.getNearestNode(network, activity.getCoord).getCoord)
        if (distanceToNetwork > maxDistanceToNetwork) return false
        prevActivityEndTime = activity.getEndTime

      case leg: Leg =>
        // Check for nighttime leg
        val legDepartureTime = leg.getDepartureTime
        if (legDepartureTime > 0.0 && legDepartureTime < prevLegDepartureTime) {
          leg.setDepartureTime(24 * 3600 + legDepartureTime)
        }
        prevLegDepartureTime = leg.getDepartureTime
      case _ =>
    })
    true
  }

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

  def copyPlanAndAddRandomChargingActivity(person: HasPlansAndId[Plan, Person]): Unit = {
    ReplanningUtil.copyPlanAndSelectForMutation(person.getSelectedPlan.getPerson)
    val chargingSequence = PopulationUtil.getChargeAtActivityBooleanSeq(person.getSelectedPlan)
    val newChargingSequence = PopulationUtil.addChargingActivityToChargingSequence(chargingSequence)
    val newChargeAtActivity = PopulationUtil.chargeAtActivityBooleanSeqToString(newChargingSequence)
    person.getSelectedPlan.getAttributes.removeAttribute("chargeAtActivity")
    person.getSelectedPlan.getAttributes.putAttribute("chargeAtActivity", newChargeAtActivity)

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
    val fixedDurationInHours = 3  // TODO Maybe randomize
    val activities: ArrayBuffer[Activity] = new ArrayBuffer()
    val legs: ArrayBuffer[Leg] = new ArrayBuffer()
    plan.getPlanElements.forEach {
      case activity: Activity => activities += activity
      case leg: Leg => legs += leg
    }
    val lastActivity = activities(activities.size - 1)
    if (activities(0).getCoord.equals(lastActivity.getCoord)) {
      plan.getPlanElements.remove(lastActivity)
      activities.remove(activities.size - 1)
    }
    else {
      // Fix plan if it does not end at home
      if (lastActivity.getEndTime < 0)
        lastActivity.setEndTime(activities(activities.size - 2).getEndTime + fixedDurationInHours*3600)
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
