# Slipstream_Test.py
# 
# Created:  Mar 2019, M. Clarke
# Modified: Jun 2021, R. Erhard

""" setup file for a cruise segment of the NASA X-57 Maxwell (Twin Engine Variant) Electric Aircraft 
"""
# ----------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------

import SUAVE
from SUAVE.Core import Units

import numpy as np
import pylab as plt
import sys

from SUAVE.Plots.Mission_Plots import *  
from SUAVE.Plots.Geometry_Plots.plot_vehicle import plot_vehicle  
from SUAVE.Plots.Geometry_Plots.plot_vehicle_vlm_panelization  import plot_vehicle_vlm_panelization

sys.path.append('../Vehicles') 
from X57_Maxwell import vehicle_setup, configs_setup 


# ----------------------------------------------------------------------
#   Main
# ----------------------------------------------------------------------
def main():
    #run test with helical fixed wake model
    helical_fixed_wake_analysis(identical_props=True)
    
    # run test with helical fixed wake model and non-identical props
    helical_fixed_wake_analysis(identical_props=False)

    # run test with bemt wake model
    bemt_wake_analysis()
    
    return 

def bemt_wake_analysis():
    # Evaluate wing in propeller wake (using helical fixed-wake model)
    bemt_wake          = True
    fixed_helical_wake = False
    configs, analyses = full_setup(bemt_wake, fixed_helical_wake, identical_props=True) 

    configs.finalize()
    analyses.finalize()  

    # mission analysis
    mission = analyses.missions.base
    results = mission.evaluate()

    # lift coefficient  
    lift_coefficient              = results.segments.cruise.conditions.aerodynamics.lift_coefficient[1][0]
    lift_coefficient_true         = 0.41741181604779815

    print(lift_coefficient)
    diff_CL                       = np.abs(lift_coefficient  - lift_coefficient_true) 
    print('CL difference')
    print(diff_CL)
    
    
    assert np.abs(lift_coefficient  - lift_coefficient_true) < 1e-6

    # sectional lift coefficient check
    sectional_lift_coeff            = results.segments.cruise.conditions.aerodynamics.lift_breakdown.inviscid_wings_sectional[0]
    sectional_lift_coeff_true       = np.array([ 4.18244032e-01,  3.40155967e-01,  3.55150658e-01,  2.95196629e-01,
                                                 1.89928151e-01,  4.18244039e-01,  3.40155855e-01,  3.55150594e-01,
                                                 2.95196655e-01,  1.89928028e-01,  2.69491655e-02,  2.86030330e-02,
                                                 2.99358393e-02,  2.95820123e-02,  2.08282714e-02,  2.69491592e-02,
                                                 2.86030338e-02,  2.99358614e-02,  2.95820665e-02,  2.08283492e-02,
                                                 6.67753211e-16,  1.36866614e-16, -3.05023682e-16, -3.67890745e-16,
                                                -2.67558659e-16])


    print(sectional_lift_coeff)
    diff_Cl   = np.abs(sectional_lift_coeff - sectional_lift_coeff_true)
    print('Cl difference')
    print(diff_Cl)
    assert  np.max(np.abs(sectional_lift_coeff - sectional_lift_coeff_true)) < 1e-6

    # plot results 
    plot_mission(results,configs.base)  

    # Plot vehicle 
    plot_vehicle(configs.base, save_figure = False, plot_control_points = False)

    # Plot vortex distribution
    plot_vehicle_vlm_panelization(configs.base, save_figure=False, plot_control_points=True)
    return

def helical_fixed_wake_analysis(identical_props):
    # Evaluate wing in propeller wake (using helical fixed-wake model)
    bemt_wake          = False
    fixed_helical_wake = True
    configs, analyses = full_setup(bemt_wake, fixed_helical_wake,identical_props) 

    configs.finalize()
    analyses.finalize()  

    # mission analysis
    mission = analyses.missions.base
    results = mission.evaluate()

    # lift coefficient  
    lift_coefficient              = results.segments.cruise.conditions.aerodynamics.lift_coefficient[1][0]
    lift_coefficient_true         = 0.4173334382292267

    print(lift_coefficient)
    diff_CL                       = np.abs(lift_coefficient  - lift_coefficient_true) 
    print('CL difference')
    print(diff_CL)
    
    assert np.abs(lift_coefficient  - lift_coefficient_true) < 1e-6

    # sectional lift coefficient check
    sectional_lift_coeff            = results.segments.cruise.conditions.aerodynamics.lift_breakdown.inviscid_wings_sectional[0]
    sectional_lift_coeff_true       = np.array([ 4.12287459e-01,  3.74505983e-01,  3.44356397e-01,  2.82577789e-01,
                                                 1.80987178e-01,  4.12287466e-01,  3.74505874e-01,  3.44356329e-01,
                                                 2.82577810e-01,  1.80987061e-01,  1.39125545e-02,  1.42214906e-02,
                                                 1.44516573e-02,  1.45807619e-02,  1.04503486e-02,  1.39125467e-02,
                                                 1.42214881e-02,  1.44516690e-02,  1.45807952e-02,  1.04503933e-02,
                                                 5.47406199e-16, -1.57415966e-17, -4.87646408e-16, -5.01339523e-16,
                                                -3.61191112e-16])


    print(sectional_lift_coeff)
    diff_Cl                       = np.abs(sectional_lift_coeff - sectional_lift_coeff_true)
    print('Cl difference')
    print(diff_Cl)
    assert  np.max(np.abs(sectional_lift_coeff - sectional_lift_coeff_true)) < 1e-6

    # plot results 
    plot_mission(results,configs.base)  

    # Plot vehicle 
    plot_vehicle(configs.base, save_figure = False, plot_control_points = False)

    # Plot vortex distribution
    plot_vehicle_vlm_panelization(configs.base, save_figure=False, plot_control_points=True)
    return
    

def plot_mission(results,vehicle): 
    
    # Plot surface pressure coefficient 
    plot_surface_pressure_contours(results,vehicle)
    
    # Plot lift distribution 
    plot_lift_distribution(results,vehicle)
    
    # Create Video Frames 
    create_video_frames(results,vehicle, save_figure = False)
    
    return


# ----------------------------------------------------------------------
#   Analysis Setup
# ----------------------------------------------------------------------

def full_setup(bemt_wake, fixed_helical_wake, identical_props):

    # vehicle data
    vehicle  = vehicle_setup() 
    
    # test for non-identical propellers
    if not identical_props:
        vehicle.networks.battery_propeller.identical_propellers = False    
    configs  = configs_setup(vehicle)

    # vehicle analyses
    configs_analyses = analyses_setup(configs, bemt_wake, fixed_helical_wake)

    # mission analyses
    mission  = mission_setup(configs_analyses,vehicle) 
    missions_analyses = missions_setup(mission)

    analyses = SUAVE.Analyses.Analysis.Container()
    analyses.configs  = configs_analyses
    analyses.missions = missions_analyses

    return configs, analyses

# ----------------------------------------------------------------------
#   Define the Vehicle Analyses
# ----------------------------------------------------------------------

def analyses_setup(configs, bemt_wake, fixed_helical_wake):

    analyses = SUAVE.Analyses.Analysis.Container()

    # build a base analysis for each config
    for tag,config in configs.items():
        analysis = base_analysis(config, bemt_wake, fixed_helical_wake)
        analyses[tag] = analysis

    return analyses

def base_analysis(vehicle, bemt_wake, fixed_helical_wake):

    # ------------------------------------------------------------------
    #   Initialize the Analyses
    # ------------------------------------------------------------------     
    analyses = SUAVE.Analyses.Vehicle()

    # ------------------------------------------------------------------
    #  Basic Geometry Relations
    sizing = SUAVE.Analyses.Sizing.Sizing()
    sizing.features.vehicle = vehicle
    analyses.append(sizing)

    # ------------------------------------------------------------------
    #  Weights
    weights = SUAVE.Analyses.Weights.Weights_Transport()
    weights.vehicle = vehicle
    analyses.append(weights)

    # ------------------------------------------------------------------
    #  Aerodynamics Analysis
    aerodynamics = SUAVE.Analyses.Aerodynamics.Fidelity_Zero()    
    if bemt_wake == True:
        aerodynamics.settings.use_surrogate             = False
        aerodynamics.settings.propeller_wake_model      = False 
        aerodynamics.settings.use_bemt_wake_model       = True
    elif fixed_helical_wake ==True:
        aerodynamics.settings.use_surrogate              = False
        aerodynamics.settings.propeller_wake_model       = True   
        aerodynamics.settings.use_bemt_wake_model        = False      

    aerodynamics.settings.number_spanwise_vortices   = 5
    aerodynamics.settings.number_chordwise_vortices  = 2   
    aerodynamics.geometry                            = vehicle
    aerodynamics.settings.drag_coefficient_increment = 0.0000
    analyses.append(aerodynamics)

    # ------------------------------------------------------------------
    #  Stability Analysis
    stability = SUAVE.Analyses.Stability.Fidelity_Zero()    
    stability.geometry = vehicle
    analyses.append(stability)

    # ------------------------------------------------------------------
    #  Energy
    energy= SUAVE.Analyses.Energy.Energy()
    energy.network = vehicle.networks 
    analyses.append(energy)

    # ------------------------------------------------------------------
    #  Planet Analysis
    planet = SUAVE.Analyses.Planets.Planet()
    analyses.append(planet)

    # ------------------------------------------------------------------
    #  Atmosphere Analysis
    atmosphere = SUAVE.Analyses.Atmospheric.US_Standard_1976()
    atmosphere.features.planet = planet.features
    analyses.append(atmosphere)   

    # done!
    return analyses    


# ----------------------------------------------------------------------
#   Define the Mission
# ----------------------------------------------------------------------

def mission_setup(analyses,vehicle):
    # ------------------------------------------------------------------
    #   Initialize the Mission
    # ------------------------------------------------------------------
    mission = SUAVE.Analyses.Mission.Sequential_Segments()
    mission.tag = 'mission'

    # airport
    airport = SUAVE.Attributes.Airports.Airport()
    airport.altitude   =  0. * Units.ft
    airport.delta_isa  =  0.0
    airport.atmosphere = SUAVE.Attributes.Atmospheres.Earth.US_Standard_1976()

    mission.airport = airport    

    # unpack Segments module
    Segments = SUAVE.Analyses.Mission.Segments 
    
    # base segment
    base_segment = Segments.Segment()
    ones_row     = base_segment.state.ones_row
    base_segment.process.iterate.initials.initialize_battery = SUAVE.Methods.Missions.Segments.Common.Energy.initialize_battery
    base_segment.process.iterate.conditions.planet_position  = SUAVE.Methods.skip
    base_segment.state.numerics.number_control_points        = 2
    
    # ------------------------------------------------------------------
    #   Climb 1 : constant Speed, constant rate segment 
    # ------------------------------------------------------------------ 
    segment = Segments.Climb.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "climb_1"
    segment.analyses.extend( analyses.base )
    segment.battery_energy            = vehicle.networks.battery_propeller.battery.max_energy* 0.89
    segment.altitude_start            = 2500.0  * Units.feet
    segment.altitude_end              = 8012    * Units.feet 
    segment.air_speed                 = 96.4260 * Units['mph'] 
    segment.climb_rate                = 700.034 * Units['ft/min']  
    segment.state.unknowns.throttle   = 0.85 * ones_row(1)
    segment = vehicle.networks.battery_propeller.add_unknowns_and_residuals_to_segment(segment)

    # add to misison
    mission.append_segment(segment)
    
    # ------------------------------------------------------------------
    #   Cruise Segment: constant Speed, constant altitude
    # ------------------------------------------------------------------ 
    segment = Segments.Cruise.Constant_Speed_Constant_Altitude(base_segment)
    segment.tag = "cruise" 
    segment.analyses.extend(analyses.base)  
    segment.air_speed                 = 135. * Units['mph'] 
    segment.distance                  = 20.  * Units.nautical_mile  
    segment.state.unknowns.throttle   = 0.85 *  ones_row(1)
    segment = vehicle.networks.battery_propeller.add_unknowns_and_residuals_to_segment(segment)
    
    # add to misison
    mission.append_segment(segment)        
    
    return mission



def missions_setup(base_mission):

    # the mission container
    missions = SUAVE.Analyses.Mission.Mission.Container()

    # ------------------------------------------------------------------
    #   Base Mission
    # ------------------------------------------------------------------

    missions.base = base_mission

    # done!
    return missions  


if __name__ == '__main__': 
    main()    
    plt.show()
