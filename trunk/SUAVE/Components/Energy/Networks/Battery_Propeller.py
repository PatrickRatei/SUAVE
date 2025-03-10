## @ingroup Components-Energy-Networks
# Battery_Propeller.py
# 
# Created:  Jul 2015, E. Botero
# Modified: Feb 2016, T. MacDonald
#           Mar 2020, M. Clarke
#           Apr 2021, M. Clarke
#           Jul 2021, E. Botero
#           Jul 2021, R. Erhard

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

# package imports
import numpy as np
from .Network import Network
from SUAVE.Components.Physical_Component import Container

from SUAVE.Core import Data , Units

# ----------------------------------------------------------------------
#  Network
# ----------------------------------------------------------------------

## @ingroup Components-Energy-Networks
class Battery_Propeller(Network):
    """ This is a simple network with a battery powering a propeller through
        an electric motor
        
        This network adds 2 extra unknowns to the mission. The first is
        a voltage, to calculate the thevenin voltage drop in the pack.
        The second is torque matching between motor and propeller.
    
        Assumptions:
        The y axis rotation is used for rotating the propeller about the Y-axis for tilt rotors and tiltwings
        
        Source:
        None
    """  
    def __defaults__(self):
        """ This sets the default values for the network to function.
    
            Assumptions:
            None
    
            Source:
            N/A
    
            Inputs:
            None
    
            Outputs:
            None
    
            Properties Used:
            N/A
        """             
        self.propeller_motors             = Container()
        self.propellers                   = Container()
        self.esc                          = None
        self.avionics                     = None
        self.payload                      = None
        self.battery                      = None
        self.nacelle_diameter             = None
        self.engine_length                = None
        self.number_of_propeller_engines  = None
        self.voltage                      = None
        self.tag                          = 'Battery_Propeller'
        self.use_surrogate                = False
        self.generative_design_minimum    = 0
        self.identical_propellers         = True
        self.thrust_angle                 = 0.
    
    # manage process with a driver function
    def evaluate_thrust(self,state):
        """ Calculate thrust given the current state of the vehicle
    
            Assumptions:
            Caps the throttle at 110% and linearly interpolates thrust off that
    
            Source:
            N/A
    
            Inputs:
            state [state()]
    
            Outputs:
            results.thrust_force_vector [newtons]
            results.vehicle_mass_rate   [kg/s]
            conditions.propulsion:
                rpm                  [radians/sec]
                current              [amps]
                battery_draw         [watts]
                battery_energy       [joules]
                voltage_open_circuit [volts]
                voltage_under_load   [volts]
                motor_torque         [N-M]
                propeller_torque     [N-M]
    
            Properties Used:
            Defaulted values
        """          
    
        # unpack
        conditions  = state.conditions
        numerics    = state.numerics
        motors      = self.propeller_motors
        props       = self.propellers
        esc         = self.esc
        avionics    = self.avionics
        payload     = self.payload
        battery     = self.battery
        num_engines = self.number_of_propeller_engines
        
        # Unpack conditions
        a = conditions.freestream.speed_of_sound
        
        # Set battery energy
        battery.current_energy = conditions.propulsion.battery_energy  

        # Step 1 battery power
        esc.inputs.voltagein = state.unknowns.battery_voltage_under_load
        
        # Step 2
        esc.voltageout(conditions)
        
        # How many evaluations to do
        if self.identical_propellers:
            n_evals = 1
            factor  = num_engines*1
        else:
            n_evals = int(num_engines)
            factor  = 1.
        
        # Setup numbers for iteration
        total_motor_current = 0.
        total_thrust        = 0. * state.ones_row(3)
        total_power         = 0.
        
        # Iterate over motor/props
        for ii in range(n_evals):
            
            # Unpack the motor and props
            motor_key = list(motors.keys())[ii]
            prop_key  = list(props.keys())[ii]
            motor     = self.propeller_motors[motor_key]
            prop      = self.propellers[prop_key]
            
            # link
            motor.inputs.voltage      = esc.outputs.voltageout 
            motor.inputs.propeller_CP = np.atleast_2d(conditions.propulsion.propeller_power_coefficient[:,ii]).T
            
            # step 3
            motor.omega(conditions)
            
            # link
            prop.inputs.omega           = motor.outputs.omega
            prop.inputs.pitch_command   = self.pitch_command
            prop.inputs.y_axis_rotation = self.thrust_angle
            
            # step 4
            F, Q, P, Cp, outputs, etap = prop.spin(conditions)
                
            # Check to see if magic thrust is needed, the ESC caps throttle at 1.1 already
            eta        = conditions.propulsion.throttle[:,0,None]
            P[eta>1.0] = P[eta>1.0]*eta[eta>1.0]
            F[eta[:,0]>1.0,:] = F[eta[:,0]>1.0,:]*eta[eta[:,0]>1.0,:]

            # Run the motor for current
            motor.current(conditions)
            
            # Conditions specific to this instantation of motor and propellers
            R                   = prop.tip_radius
            rpm                 = motor.outputs.omega / Units.rpm
            F_mag               = np.atleast_2d(np.linalg.norm(F, axis=1)).T
            total_thrust        = total_thrust + F * factor
            total_power         = total_power  + P * factor
            total_motor_current = total_motor_current + factor*motor.outputs.current

            # Pack specific outputs
            conditions.propulsion.propeller_motor_torque[:,ii] = motor.outputs.torque[:,0]
            conditions.propulsion.propeller_torque[:,ii]       = Q[:,0]
            conditions.propulsion.propeller_rpm[:,ii]          = rpm[:,0]
            conditions.propulsion.propeller_tip_mach[:,ii]     = (R*rpm[:,0]*Units.rpm)/a[:,0]
            conditions.propulsion.disc_loading[:,ii]           = (F_mag[:,0])/(np.pi*(R**2)) # N/m^2                  
            conditions.propulsion.power_loading[:,ii]          = (F_mag[:,0])/(P[:,0])      # N/W      
            conditions.propulsion.propeller_efficiency         = etap[:,0]      
            
            conditions.noise.sources.propellers[prop.tag]      = outputs

        # Run the avionics
        avionics.power()

        # Run the payload
        payload.power()
        
        # link
        esc.inputs.currentout = total_motor_current

        # Run the esc
        esc.currentin(conditions)

        # Calculate avionics and payload power
        avionics_payload_power = avionics.outputs.power + payload.outputs.power

        # Calculate avionics and payload current
        avionics_payload_current = avionics_payload_power/self.voltage

        # link
        battery.inputs.current  = esc.outputs.currentin + avionics_payload_current
        battery.inputs.power_in = -(esc.outputs.voltageout*esc.outputs.currentin + avionics_payload_power)
        battery.energy_calc(numerics)        
    
        # Pack the conditions for outputs
        conditions.propulsion.battery_current              = esc.outputs.currentin
        conditions.propulsion.battery_draw                 = battery.inputs.power_in 
        conditions.propulsion.battery_energy               = battery.current_energy
        conditions.propulsion.battery_voltage_open_circuit = battery.voltage_open_circuit
        conditions.propulsion.battery_voltage_under_load   = battery.voltage_under_load
        conditions.propulsion.state_of_charge              = battery.state_of_charge
        conditions.propulsion.battery_specfic_power        = -battery.inputs.power_in/battery.mass_properties.mass #Wh/kg
    
        # Create the outputs
        results = Data()
        results.thrust_force_vector = total_thrust
        results.vehicle_mass_rate   = state.ones_row(1)*0.0
        
        return results
    
    
    def unpack_unknowns(self,segment):
        """ This is an extra set of unknowns which are unpacked from the mission solver and send to the network.
    
            Assumptions:
            None
    
            Source:
            N/A
    
            Inputs:
            state.unknowns.propeller_power_coefficient [None]
            state.unknowns.battery_voltage_under_load  [volts]
    
            Outputs:
            state.conditions.propulsion.propeller_power_coefficient [None]
            state.conditions.propulsion.battery_voltage_under_load  [volts]
    
            Properties Used:
            N/A
        """                  
        
        # Here we are going to unpack the unknowns (Cp) provided for this network
        ss = segment.state
        ss.conditions.propulsion.propeller_power_coefficient = ss.unknowns.propeller_power_coefficient
        ss.conditions.propulsion.battery_voltage_under_load  = ss.unknowns.battery_voltage_under_load
        
        return
    
    def residuals(self,segment):
        """ This packs the residuals to be send to the mission solver.
    
            Assumptions:
            None
    
            Source:
            N/A
    
            Inputs:
            state.conditions.propulsion:
                motor_torque                          [N-m]
                propeller_torque                      [N-m]
                voltage_under_load                    [volts]
            state.unknowns.battery_voltage_under_load [volts]
            
            Outputs:
            None
    
            Properties Used:
            self.voltage                              [volts]
        """        
        
        # Here we are going to pack the residuals (torque,voltage) from the network
        
        # Unpack
        q_motor   = segment.state.conditions.propulsion.propeller_motor_torque
        q_prop    = segment.state.conditions.propulsion.propeller_torque
        v_actual  = segment.state.conditions.propulsion.battery_voltage_under_load
        v_predict = segment.state.unknowns.battery_voltage_under_load
        v_max     = self.voltage
        
        # Return the residuals
        segment.state.residuals.network[:,0]  = (v_predict[:,0] - v_actual[:,0])/v_max
        segment.state.residuals.network[:,1:] = q_motor - q_prop
        
        return    
    
    
    def add_unknowns_and_residuals_to_segment(self, segment, initial_voltage = None, initial_power_coefficient = 0.005):
        """ This function sets up the information that the mission needs to run a mission segment using this network
    
            Assumptions:
            None
    
            Source:
            N/A
    
            Inputs:
            segment
            initial_voltage                   [v]
            initial_power_coefficient         [float]s
            
            Outputs:
            segment.state.unknowns.battery_voltage_under_load
            segment.state.unknowns.propeller_power_coefficient
            segment.state.conditions.propulsion.propeller_motor_torque
            segment.state.conditions.propulsion.propeller_torque   
    
            Properties Used:
            N/A
        """           
        
        # unpack the ones function
        ones_row = segment.state.ones_row
        
        # unpack the initial values if the user doesn't specify
        if initial_voltage==None:
            initial_voltage = self.battery.max_voltage
        
        # Count how many unknowns and residuals based on p
        n_props  = len(self.propellers)
        n_motors = len(self.propeller_motors)
        n_eng    = self.number_of_propeller_engines
        
        if n_props!=n_motors!=n_eng:
            print('The number of propellers is not the same as the number of motors')
            
        # Now check if the propellers are all identical, in this case they have the same of residuals and unknowns
        if self.identical_propellers:
            n_props = 1
            
        # number of residuals, props plus the battery voltage
        n_res = n_props + 1
        
        # Setup the residuals
        segment.state.residuals.network = 0. * ones_row(n_res)
        
        # Setup the unknowns
        segment.state.unknowns.battery_voltage_under_load  = initial_voltage * ones_row(1)
        segment.state.unknowns.propeller_power_coefficient = initial_power_coefficient * ones_row(n_props)
        
        # Setup the conditions
        segment.state.conditions.propulsion.propeller_motor_torque = 0. * ones_row(n_props)
        segment.state.conditions.propulsion.propeller_torque       = 0. * ones_row(n_props)
        segment.state.conditions.propulsion.propeller_rpm          = 0. * ones_row(n_props)
        segment.state.conditions.propulsion.disc_loading           = 0. * ones_row(n_props)                 
        segment.state.conditions.propulsion.power_loading          = 0. * ones_row(n_props)
        segment.state.conditions.propulsion.propeller_tip_mach     = 0. * ones_row(n_props)
        segment.state.conditions.propulsion.propeller_efficiency   = 0. * ones_row(n_props)        
        
        # Ensure the mission knows how to pack and unpack the unknowns and residuals
        segment.process.iterate.unknowns.network  = self.unpack_unknowns
        segment.process.iterate.residuals.network = self.residuals        

        return segment
            
    __call__ = evaluate_thrust


