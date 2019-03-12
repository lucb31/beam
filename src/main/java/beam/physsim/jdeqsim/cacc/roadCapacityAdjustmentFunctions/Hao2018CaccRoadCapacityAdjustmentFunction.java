package beam.physsim.jdeqsim.cacc.roadCapacityAdjustmentFunctions;

import beam.physsim.jdeqsim.cacc.roadCapacityAdjustmentFunctions.RoadCapacityAdjustmentFunction;
import beam.utils.DebugLib;
import org.matsim.api.core.v01.network.Link;


/*

CACC regression function derived from (Figure 8, Simulation):

Liu, Hao, et al. "Modeling impacts of Cooperative Adaptive Cruise Control on mixed traffic flow
in multi-lane freeway facilities." Transportation Research Part C: Emerging Technologies 95 (2018): 261-279.

 */

public class Hao2018CaccRoadCapacityAdjustmentFunction implements RoadCapacityAdjustmentFunction {

    private int caccMinRoadCapacity;
    private double caccMinSpeedMetersPerSec;

    public Hao2018CaccRoadCapacityAdjustmentFunction(int caccMinRoadCapacity, double caccMinSpeedMetersPerSec){

        this.caccMinRoadCapacity = caccMinRoadCapacity;
        this.caccMinSpeedMetersPerSec = caccMinSpeedMetersPerSec;
    }

    public double getCapacityWithCACC(Link link, double fractionCACCOnRoad){
        double initialCapacity=link.getFlowCapacityPerSec();

        if (fractionCACCOnRoad>0 && fractionCACCOnRoad<1.0){
            DebugLib.emptyFunctionForSettingBreakPoint();
        }


        if (initialCapacity>=caccMinRoadCapacity && link.getFreespeed()>caccMinSpeedMetersPerSec) {
            return (2152.777778 * fractionCACCOnRoad * fractionCACCOnRoad * fractionCACCOnRoad - 764.8809524 * fractionCACCOnRoad * fractionCACCOnRoad + 456.1507937 * fractionCACCOnRoad + 1949.047619) / 1949.047619 * initialCapacity;

        } else {
           return initialCapacity;
        }

    }
}
