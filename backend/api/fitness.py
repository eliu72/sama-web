import numpy as np
from math import ceil

from api.input_data import *
from api.ems import energy_management


def fitness(X, input_data, final_solution=False):

    if X.size==1:
        X=X[0]
    
    NT=input_data.Eload.size         # time step numbers
    Npv=round(X[0])       # PV number
    Nwt=round(X[1])       # WT number
    Nbat=round(X[2])      # Battery pack number
    N_DG=round(X[3])      # number of Diesel Generator
    Cn_I=X[4]             # Inverter Capacity
    
    Pn_PV=Npv*Ppv_r    # PV Total Capacity
    Pn_WT=Nwt*Pwt_r    # WT Total Capacity
    Cn_B=Nbat*Cbt_r    # Battery Total Capacity
    Pn_DG=N_DG*Cdg_r   # Diesel Total Capacity
    
    # PV Power Calculation
    Tc   = input_data.T+(((Tnoct-20)/800)*input_data.G) # Module Temprature
    Ppv = fpv*Pn_PV*(input_data.G/Gref)*(1+Tcof*(Tc-Tref)) # output power(kw)_hourly
    
    # Wind turbine Power Calculation
    v1=input_data.Vw     #hourly wind speed
    v2=((h_hub/h0)**(alfa_wind_turbine))*v1 # v1 is the speed at a reference height;v2 is the speed at a hub height h2
    
    Pwt=np.zeros(8760)
    true_value=np.logical_and(v_cut_in<=v2,v2<v_rated)
    Pwt[np.logical_and(v_cut_in<=v2,v2<v_rated)]=v2[true_value]**3 *(Pwt_r/(v_rated**3-v_cut_in**3))-(v_cut_in**3/(v_rated**3-v_cut_in**3))*(Pwt_r)
    Pwt[np.logical_and(v_rated<=v2,v2<v_cut_out)]=Pwt_r
    Pwt=Pwt*Nwt
    
    
    ## Energy Management 
    # Battery Wear Cost
    Cbw = R_B*Cn_B/(Nbat*Q_lifetime*np.sqrt(ef_bat)) if Cn_B > 0 else 0
    
    #  DG Fix cost
    cc_gen=b*Pn_DG*C_fuel+R_DG*Pn_DG/TL_DG+MO_DG;

    Pdg, Ens, Pbuy, Psell, Edump, Pch, Pdch, Eb = energy_management(Ppv,Pwt,input_data.Eload,Cn_B,Nbat,Pn_DG,NT,
        SOC_max,SOC_min,SOC_initial,n_I,Grid,Cbuy,a,Cn_I,LR_DG,C_fuel,input_data.Pbuy_max,input_data.Psell_max,cc_gen,Cbw,
        self_discharge_rate,alfa_battery,c,k,Imax,Vnom,ef_bat)
    
    q=(a*Pdg+b*Pn_DG)*(Pdg>0)   # Fuel consumption of a diesel generator 
    
    ## Installation and operation cost
    
    # Total Investment cost ($)
    I_Cost=input_data.pv_cost*Pn_PV + C_WT*Pn_WT+ input_data.diesel_generator_cost*Pn_DG+input_data.battery_cost*Cn_B+input_data.battery_charger_cost*Cn_I +C_CH
    
    Top_DG=np.sum(Pdg>0)+1
    L_DG=TL_DG/Top_DG
    RT_DG=ceil(n/L_DG)-1 #Replecement time
    
    #Total Replacement cost ($)
    RC_PV= np.zeros(n)
    RC_WT= np.zeros(n)
    RC_DG= np.zeros(n)
    RC_B = np.zeros(n)
    RC_I = np.zeros(n)
    RC_CH = np.zeros(n)
    
    RC_PV[np.arange(L_PV+1,n,L_PV)]= R_PV*Pn_PV/(1+ir)**(np.arange(1.001*L_PV,n,L_PV)) 
    RC_WT[np.arange(L_WT+1,n,L_WT)]= R_WT*Pn_WT/(1+ir)** (np.arange(1.001*L_WT,n,L_WT)) 
    RC_DG[np.arange(L_DG+1,n,L_DG).astype(np.int32)]= R_DG*Pn_DG/(1+ir)**(np.arange(1.001*L_DG,n,L_DG)) 
    RC_B[np.arange(L_B+1,n,L_B)] = R_B*Cn_B /(1+ir)**(np.arange(1.001*L_B,n,L_B)) 
    RC_I[np.arange(L_I+1,n,L_I)] = R_I*Cn_I /(1+ir)**(np.arange(1.001*L_I,n,L_I)) 
    RC_CH[np.arange(L_CH+1,n,L_CH)]  = R_CH /(1+ir)**(np.arange(1.001*L_CH,n,L_CH)) 
    R_Cost=RC_PV+RC_WT+RC_DG+RC_B+RC_I+RC_CH
    
    #Total M&O Cost ($/year)
    MO_Cost=(MO_PV*Pn_PV + MO_WT*Pn_WT+ MO_DG*np.sum(Pn_DG>0)+ \
             MO_B*Cn_B+ MO_I*Cn_I +MO_CH)/(1+ir)**np.array(range(1,n+1))
    
    # DG fuel Cost
    C_Fu= np.sum(C_fuel*q)/(1+ir)**np.array(range(1,n+1))
    
    # Salvage
    L_rem=(RT_PV+1)*L_PV-n 
    S_PV=(R_PV*Pn_PV)*L_rem/L_PV * 1/(1+ir)**n # PV
    L_rem=(RT_WT+1)*L_WT-n
    S_WT=(R_WT*Pn_WT)*L_rem/L_WT * 1/(1+ir)**n # WT
    L_rem=(RT_DG+1)*L_DG-n 
    S_DG=(R_DG*Pn_DG)*L_rem/L_DG * 1/(1+ir)**n # DG
    L_rem=(RT_B +1)*L_B-n 
    S_B =(R_B*Cn_B)*L_rem/L_B * 1/(1+ir)**n
    L_rem=(RT_I +1)*L_I-n
    S_I =(R_I*Cn_I)*L_rem/L_I * 1/(1+ir)**n
    L_rem=(RT_CH +1)*L_CH-n
    S_CH =(R_CH)*L_rem/L_CH * 1/(1+ir)**n
    Salvage=S_PV+S_WT+S_DG+S_B+S_I+S_CH
    
    
    # Emissions produced by Disesl generator (g)
    DG_Emissions=np.sum(q*(CO2 + NOx + SO2))/1000           # total emissions (kg/year)
    Grid_Emissions= np.sum(Pbuy*(E_CO2+E_SO2+E_NOx))/1000    # total emissions (kg/year)
    
    Grid_Cost= (np.sum(Pbuy*Cbuy)-np.sum(Psell*Csell))* 1/(1+ir)**np.array(range(1,n+1))
    
    #Capital recovery factor
    CRF=ir*(1+ir)**n/((1+ir)**n -1)
    
    # Totall Cost
    temp = np.sum(R_Cost)+ np.sum(MO_Cost)+np.sum(C_Fu) -Salvage+np.sum(Grid_Cost)
    NPC=I_Cost+temp
    Operating_Cost=CRF*temp
    
    if np.sum(input_data.Eload-Ens)>1:
        LCOE=CRF*NPC/np.sum(input_data.Eload-Ens+Psell)                #Levelized Cost of Energy ($/kWh)
        LEM=(DG_Emissions+Grid_Emissions)/sum(input_data.Eload-Ens)    #Levelized Emissions(kg/kWh)
    else:
        LCOE=100
        LEM=100
    
    LPSP=np.sum(Ens)/np.sum(input_data.Eload)
    
    RE=1-np.sum(Pdg+Pbuy)/np.sum(input_data.Eload+Psell-Ens)
    if(np.isnan(RE)):
        RE=0
    
    if final_solution == True:
        Investment=np.zeros(n)
        Investment[0]=I_Cost
        Salvage1 = np.zeros(n)
        Salvage1[-1] = Salvage
        Salage = Salvage1

        Operating=np.zeros(n)
        Operating[0:n+1]=MO_PV*Pn_PV + MO_WT*Pn_WT+ MO_DG\
            *Pn_DG+ MO_B*Cn_B+ MO_I*Cn_I+np.sum(Pbuy*Cbuy)-np.sum(Psell*Csell)
        
        Fuel=np.zeros(n)
        Fuel[0:n+1]=np.sum(C_fuel*q)

        RC_PV[np.arange(L_PV+1,n,L_PV)]= R_PV*Pn_PV
        RC_WT[np.arange(L_WT+1,n,L_WT)]=R_WT*Pn_WT 
        RC_DG[np.arange(L_DG+1,n,L_DG).astype(np.int32)]= R_DG*Pn_DG
        RC_B[np.arange(L_B+1,n,L_B)] = R_B*Cn_B
        RC_I[np.arange(L_I+1,n,L_I)] =R_I*Cn_I 
        Replacement=RC_PV+RC_WT+RC_DG+RC_B+RC_I

        Cash_Flow=np.zeros((n,5))
        Cash_Flow[:,0]=-Investment
        Cash_Flow[:,1]=-Operating
        Cash_Flow[:,2]=Salvage
        Cash_Flow[:,3]=-Fuel
        Cash_Flow[:,4]=-Replacement

        result = {}
        
        # System size
        result["PV Capacity"] = (Pn_PV, "kW")
        result["WT Capacity"] = (Pn_WT, "kW")
        result["Battery Capacity"] = (Cn_B, "kWh")
        result["Diesel Capacity"] = (Pn_DG, "kW")
        result["Inverter Capacity"] = (Cn_I, "kW")

        # Result
        result["NPC"] = (NPC, "$")
        result["Levelized Cost of Electricity"] = (LCOE, "$/kWh")
        result["Operation Cost"] = (Operating_Cost, "$")
        result["Initial Cost"] = (I_Cost, "$")
        result["RE"] = (RE*100, "%")
        result["Total operation and maintenance cost"] = (np.sum(MO_Cost), "$")

        result["LPSP"] = (LPSP*100, "%")
        result["excess Electricity"] = (np.sum(Edump), "")

        result["Total power bought from Grid"] = (np.sum(Pbuy), "kWh")
        result["Total Money paid to the Grid"] = (np.sum(Grid_Cost), "$")
        result["Total money paid by the user"] = (np.sum(NPC), "$")
        result["Grid sales"] = (np.sum(Psell), "kWh")
        result["LEM"] = (LEM, "kg/kWh")
        result["PV Power"] = (np.sum(Ppv), "kWh")
        result["WT Power"] = (np.sum(Pwt), "kWh")
        result["Diesel Generator Power"] = (np.sum(Pdg), "kWh")
        result["Total fuel consumed by DG"] = (np.sum(q), "kg/year")

        result["DG Emissions"] = (DG_Emissions, "kg/year")
        result["Grid Emissions"] = (Grid_Emissions, "kg/year")

        return result, Cash_Flow, Pbuy, Psell, input_data.Eload, Ens, Pdg, Pch, Pdch, Ppv, Pwt, Eb, Cn_B, Edump

    Z=LCOE+EM*LEM+10*(LPSP>LPSP_max)+10*(RE<RE_min)+100*(I_Cost>Budget)+\
        100*max(0, LPSP-LPSP_max)+100*max(0, RE_min-RE)+100*max(0, I_Cost-Budget)

    return Z
