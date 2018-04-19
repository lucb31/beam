package beam.agentsim.agents.rideHail

import beam.agentsim.agents.rideHail.RideHailingManager.{RideHailingAgentLocation, RideHailingInquiry}
import beam.agentsim.events.SpaceTime
import org.matsim.api.core.v01.Id
import org.matsim.vehicles.Vehicle

class DefaultRideHailResourceAllocationManager extends RideHailResourceAllocationManager {

  val isBufferedRideHailAllocationMode = false

  def getVehicleAllocation(vehicleAllocationRequest: VehicleAllocationRequest): Option[VehicleAllocation] = {
    None
  }

// TODO RW/Asif: how to make sure no one ever can call this?
def allocateVehiclesInBatch(allocationsDuringReservation: Map[Id[RideHailingInquiry], Option[(VehicleAllocation, RideHailingAgentLocation)]]): Map[Id[RideHailingInquiry], Option[VehicleAllocation]] = {
  log.error("batch processing is not implemented for DefaultRideHailResourceAllocationManager")
    ???
  }

  override def getVehiclesToReposition(tick: Double): Vector[(Id[Vehicle], SpaceTime)] = {
    Vector()
  }
}




