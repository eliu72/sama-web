import numpy as np
from math import ceil

"""
TODO: Get rid of globals!
This module exports all variables as globals. 
It is bad practice to use globals because they are module-scoped.
Better practice to use objects - store all variables as class variables.
"""

class Input():
    def __init__(
        self, 
        residential_load_data, 
        hourly_plane_of_irradiance, 
        hourly_ambient_temperature, 
        hourly_windspeed,
        pv_cost,
        diesel_generator_cost,
        battery_cost,
        battery_charger_cost
    ):
        # need 8760 hours of data
        self.Eload = residential_load_data # we need the OpenAI data - hourly electrical load
        self.G = np.array(hourly_plane_of_irradiance) #Data[:,1] # hourly plane of array irradiance - PVWatts
        self.T = np.array(hourly_ambient_temperature) #Data[:,2] # hourly ambient temperature - PVWatts
        self.Vw = np.array(hourly_windspeed) #Data[:,3] # hourly windspeed - PVWatts
        
        self.Pbuy_max=ceil(1.2*max(self.Eload)) # kWh
        self.Psell_max=self.Pbuy_max

        # Use default values if input params from request are None
        self.pv_cost = float(pv_cost) or 896
        self.diesel_generator_cost = float(diesel_generator_cost) or 352
        self.battery_cost = float(battery_cost) or 360
        self.battery_charger_cost = float(battery_charger_cost) or 150


def calcTouCbuy(day, month):
    P_peak=0.17
    P_mid=0.113
    P_offpeak=0.083
    Cbuy=np.zeros(8760)

    # Winter
    Tp_w=np.array([7,8,9,10,17,18])
    Tm_w=np.array(range(11,17))
    Toff_w=np.array([1,2,3,4,5,6,19,20,21,22,23,24])

    #Summer
    Tp_s=np.array([11,12,13,14,15,16])
    Tm_s=np.array([7,8,9,10,17,18])
    Toff_s=np.array([1,2,3,4,5,6,19,20,21,22,23,24])

    for m in range(1,13):
        t_start=(24*sum(day[0:m-1])+1)
        t_end=(24*sum(day[0:m]))
        t_index=np.array(range(t_start,t_end+1))
        if month[m-1]==1:   #for summer
            tp=Tp_s
            tm=Tm_s
            toff=Toff_s
        else:               #for winter
            tp=Tp_w
            tm=Tm_w
            toff=Toff_w
        
        Cbuy[t_index-1]=P_offpeak
        for d in range(1,day[m-1]+1):
            idx0=np.array(t_index[tp]+24*(d-1))-1
            Cbuy[idx0-1]=P_peak
            idx1=np.array(t_index[tm]+24*(d-1))-1
            Cbuy[idx1-1]=P_mid
           
    return Cbuy

#Type of system (1: included, 0=not included)
PV=1
WT=1
DG=1
Bat=1
Grid=0
EM=0  # 0: LCOE, 1:LCOE+LEM
Budget=200e3    # Limit On Total Capital Cost

# %%
n = 25;                  # life year of system (year)
n_ir=0.0473;             # Nominal discount rate
e_ir=0.02;               # Expected inflation rate
ir=(n_ir-e_ir)/(1+e_ir); # real discount rate
LPSP_max=0.011; # Maximum loss of power supply probability
RE_min=0.75;    # minimum Renewable Energy
Ppv_r=0.500;  # PV module rated power (kW)
Pwt_r=1;      # WT rated power (kW)
Cbt_r=1;      # Battery rated Capacity (kWh)
Cdg_r=0.5;   # Battery rated Capacity (kWh)
#%% PV data
# hourly_solar_radiation W
fpv=0.9;       # the PV derating factor [%]
Tcof=0;        # temperature coefficient
Tref=25;       # temperature at standard test condition
Tnoct=45;      # Nominal operating cell temperature
Gref = 1000 ;  # 1000 W/m^2
C_PV = 896 ;      # Capital cost ($) per KW
R_PV = 896;       # Replacement Cost of PV modules Per KW
MO_PV = 12 ;      # O&M  cost ($/year/kw)
L_PV=25;          # Life time (year)
n_PV=0.205;       # Efficiency of PV module
D_PV=0.01;        # PV yearly degradation
CE_PV=50;         # Engineering cost of system per kW for first year
RT_PV=ceil(n/L_PV)-1   # Replecement time

#%% WT data
h_hub=17;               # Hub height 
h0=43.6;                # anemometer height
nw=1;                   # Electrical Efficiency
v_cut_out=25;           # cut out speed
v_cut_in=2.5;           # cut in speed
v_rated=9.5;            # rated speed(m/s)
alfa_wind_turbine=0.14; # coefficient of friction ( 0.11 for extreme wind conditions, and 0.20 for normal wind conditions)
C_WT = 1200;      # Capital cost ($) per KW
R_WT = 1200;      # Replacement Cost of WT Per KW
MO_WT = 40 ;      # O&M  cost ($/year/kw)
L_WT=20;          # Life time (year)
n_WT=0.30;        # Efficiency of WT module
D_WT=0.05;        # WT yearly degradation
RT_WT=ceil(n/L_WT)-1   # Replecement time

#%% Diesel generator
C_DG = 352;       # Capital cost ($/KWh)
R_DG = 352;       # Replacement Cost ($/kW)
MO_DG = 0.003;    # O&M+ running cost ($/op.h)
TL_DG=131400;      # Life time (h)
n_DG=0.4;         # Efficiency
D_DG=0.05;        # yearly degradation (%)
LR_DG=0.25;        # Minimum Load Ratio (%)
C_fuel=1.24;  # Fuel Cost ($/L)
## Diesel Generator fuel curve
a=0.2730;          # L/hr/kW output
b=0.0330;          # L/hr/kW rated
#% Emissions produced by Disesl generator for each fuel in littre [L]	g/L
CO2=2621.7;
CO = 16.34;
NOx = 6.6;
SO2 = 20;

#%% Battery data
C_B = 360;              # Capital cost ($/KWh)
R_B = 360;              # Repalacement Cost ($/kW)
MO_B=10;                # Maintenance cost ($/kw.year)
L_B=5;                  # Life time (year)
SOC_min=0.2;
SOC_max=1;
SOC_initial=0.5;
D_B=0.05;               # Degradation
RT_B=ceil(n/L_B)-1;     # Replecement time
Q_lifetime=8000;        # kWh
self_discharge_rate=0;  # Hourly self-discharge rate
alfa_battery=1;         # is the storage's maximum charge rate [A/Ah]
c=0.403;                # the storage capacity ratio [unitless] 
k=0.827;                # the storage rate constant [h-1]
Imax=16.7;              # the storage's maximum charge current [A]
Vnom=12;                # the storage's nominal voltage [V] 
ef_bat=0.8;             # storage DC-DC efficiency 
#%% Inverter
C_I = 788;        # Capital cost ($/kW)
R_I = 788;        # Replacement cost ($/kW)
MO_I =20;         # O&M cost ($/kw.year)
L_I=25;           # Life time (year)
n_I=0.85;         # Efficiency
RT_I=ceil(n/L_I)-1; # Replecement time

# %% Charger
#New edits
if Bat==1:
    C_CH = 150;  # Capital Cost ($)
    R_CH = 150;  # Replacement Cost ($)
    MO_CH = 5;   # O&M cost ($/year)
    L_CH=25;     # Life time (year)
    RT_CH=ceil(n/L_CH)-1; # Replecement time
else:
    C_CH = 0;  # Capital Cost ($)
    R_CH = 0;  # Replacement Cost ($)
    MO_CH = 0;   # O&M cost ($/year)
    L_CH=25;     # Life time (year)
    RT_CH=ceil(n/L_CH)-1; # Replecement time


# calculate Cbuy
months = np.zeros(13)
months[4:10]=1; # Summer
daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

Cbuy = calcTouCbuy(daysInMonth, months)
Csell = 0.1

## Emissions produced by Grid generators (g/kW)
E_CO2=1.43;
E_SO2=0.01;
E_NOx=0.39;