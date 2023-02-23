#
# Import the ParFlow TCL package
#
lappend auto_path $env(PARFLOW_DIR)/bin 
package require parflow
namespace import Parflow::*

foreach dir {qflx_evap_grnd eflx_lh_tot qflx_evap_tot qflx_tran_veg correct_output qflx_infl swe_out eflx_lwrad_out t_grnd diag_out qflx_evap_soi eflx_soil_grnd eflx_sh_tot qflx_evap_veg qflx_top_soil} {
    file mkdir $dir
}

pfset FileVersion 4

pfset Process.Topology.P 1
pfset Process.Topology.Q 1
pfset Process.Topology.R 1

#pfset Process.Command ""

#---------------------------------------------------------
# Computational Grid
#---------------------------------------------------------
pfset ComputationalGrid.Lower.X           0.0
pfset ComputationalGrid.Lower.Y           0.0
pfset ComputationalGrid.Lower.Z           0.0

pfset ComputationalGrid.NX                10
pfset ComputationalGrid.NY                 1
pfset ComputationalGrid.NZ                10

pfset ComputationalGrid.DX	       100.0
pfset ComputationalGrid.DY               100.0
pfset ComputationalGrid.DZ	         1.0

set nx [pfget ComputationalGrid.NX]
set dx [pfget ComputationalGrid.DX]
set ny [pfget ComputationalGrid.NY]
set dy [pfget ComputationalGrid.DY]
set nz [pfget ComputationalGrid.NZ]
set dz [pfget ComputationalGrid.DZ]

#---------------------------------------------------------
# The Names of the GeomInputs
#---------------------------------------------------------
pfset GeomInput.Names                 "boxinput riverinput hillslopeinput"

pfset GeomInput.boxinput.InputType Box
pfset GeomInput.boxinput.GeomName domain

pfset GeomInput.riverinput.InputType Box
pfset GeomInput.riverinput.GeomName river

pfset GeomInput.hillslopeinput.InputType Box
pfset GeomInput.hillslopeinput.GeomName hillslope

#---------------------------------------------------------
# Domain Geometry
#---------------------------------------------------------
pfset Geom.domain.Lower.X                        0.0
pfset Geom.domain.Lower.Y                        0.0
pfset Geom.domain.Lower.Z                        0.0

pfset Geom.domain.Upper.X                     1000.0
pfset Geom.domain.Upper.Y                        100.0
pfset Geom.domain.Upper.Z                       10.0

pfset Geom.domain.Patches "left right front back bottom top"

pfset Geom.river.Lower.X                        0.0
pfset Geom.river.Lower.Y                        0.0
pfset Geom.river.Lower.Z                        0.0

pfset Geom.river.Upper.X                     100.0
pfset Geom.river.Upper.Y                       100.0
pfset Geom.river.Upper.Z                       10.0

pfset Geom.hillslope.Lower.X                      100.0
pfset Geom.hillslope.Lower.Y                        0.0
pfset Geom.hillslope.Lower.Z                        0.0

pfset Geom.hillslope.Upper.X                    1000.0
pfset Geom.hillslope.Upper.Y                        100.0
pfset Geom.hillslope.Upper.Z                       10.0
#--------------------------------------------
# variable dz assignments
#------------------------------------------
pfset Solver.Nonlinear.VariableDz     True
#pfset Solver.Nonlinear.VariableDz     False 
pfset dzScale.GeomNames            domain
pfset dzScale.Type            nzList
pfset dzScale.nzListNumber       10
pfset Cell.0.dzScale.Value 1.28
pfset Cell.1.dzScale.Value 1.28
pfset Cell.2.dzScale.Value 1.28
pfset Cell.3.dzScale.Value 1.28
pfset Cell.4.dzScale.Value 0.64
pfset Cell.5.dzScale.Value 0.32
pfset Cell.6.dzScale.Value 0.16
pfset Cell.7.dzScale.Value 0.08
pfset Cell.8.dzScale.Value 0.04
pfset Cell.9.dzScale.Value 0.02

#-----------------------------------------------------------------------------
# Perm
#-----------------------------------------------------------------------------
pfset Geom.Perm.Names                 domain
# Permeability coefficient k set in [m/h]
pfset Geom.domain.Perm.Type            Constant
pfset Geom.domain.Perm.Value           1
# k [m/s] = 0.01/3600 = 2.78 E-06
# Moderate permeability : very fine sands, mixtures of sand, silt and clay
# k [m/s] = 1/3600 = 2.78 E -04
# Good permeability : sands

#-----------------------------------------------------------------------------
# Perm Tensors
#-----------------------------------------------------------------------------

pfset Perm.TensorType               TensorByGeom

pfset Geom.Perm.TensorByGeom.Names  "domain"

pfset Geom.domain.Perm.TensorValX  1.0d0
pfset Geom.domain.Perm.TensorValY  1.0d0
pfset Geom.domain.Perm.TensorValZ  1.0d0

#-----------------------------------------------------------------------------
# Specific Storage
#-----------------------------------------------------------------------------

pfset SpecificStorage.Type            Constant
pfset SpecificStorage.GeomNames       "domain"
pfset Geom.domain.SpecificStorage.Value 0.0001

#-----------------------------------------------------------------------------
# Phases
#-----------------------------------------------------------------------------

pfset Phase.Names "water"

pfset Phase.water.Density.Type	        Constant
pfset Phase.water.Density.Value	        1.0

pfset Phase.water.Viscosity.Type	Constant
pfset Phase.water.Viscosity.Value	1.0

#-----------------------------------------------------------------------------
# Contaminants
#-----------------------------------------------------------------------------

pfset Contaminants.Names			""

#-----------------------------------------------------------------------------
# Retardation
#-----------------------------------------------------------------------------

pfset Geom.Retardation.GeomNames           ""

#-----------------------------------------------------------------------------
# Gravity
#-----------------------------------------------------------------------------

pfset Gravity				1.0

#-----------------------------------------------------------------------------
# Setup timing info
#-----------------------------------------------------------------------------
pfset TimingInfo.BaseUnit               1.0
pfset TimingInfo.StartCount             0
pfset TimingInfo.StartTime              0.0
# 1 years
pfset TimingInfo.StopTime               17520.0
pfset TimingInfo.DumpInterval           24.0
pfset TimeStep.Type                     Constant
pfset TimeStep.Value                    1.0

#-----------------------------------------------------------------------------
# Porosity
#-----------------------------------------------------------------------------

pfset Geom.Porosity.GeomNames           domain
pfset Geom.domain.Porosity.Type          Constant
pfset Geom.domain.Porosity.Value         0.415

#-----------------------------------------------------------------------------
# Domain
#-----------------------------------------------------------------------------

pfset Domain.GeomName domain

#-----------------------------------------------------------------------------
# Relative Permeability
#-----------------------------------------------------------------------------

pfset Phase.RelPerm.Type               VanGenuchten
pfset Phase.RelPerm.GeomNames          domain

pfset Geom.domain.RelPerm.Alpha         1.
pfset Geom.domain.RelPerm.N             2. 

#---------------------------------------------------------
# Saturation
#---------------------------------------------------------

pfset Phase.Saturation.Type              VanGenuchten
pfset Phase.Saturation.GeomNames         domain

pfset Geom.domain.Saturation.Alpha        1.
pfset Geom.domain.Saturation.N            2.0
pfset Geom.domain.Saturation.SRes         0.2
pfset Geom.domain.Saturation.SSat         1.0

#-----------------------------------------------------------------------------
# Wells
#-----------------------------------------------------------------------------
pfset Wells.Names                           ""

#-----------------------------------------------------------------------------
# Time Cycles
#-----------------------------------------------------------------------------
pfset Cycle.Names constant
pfset Cycle.constant.Names              "alltime"
pfset Cycle.constant.alltime.Length      1
pfset Cycle.constant.Repeat             -1
 
#-----------------------------------------------------------------------------
# Boundary Conditions: Pressure
#-----------------------------------------------------------------------------
pfset BCPressure.PatchNames        "left right front back bottom top"

pfset Patch.left.BCPressure.Type                      FluxConst
pfset Patch.left.BCPressure.Cycle                     "constant"
pfset Patch.left.BCPressure.alltime.Value             0.0

pfset Patch.right.BCPressure.Type                      FluxConst
pfset Patch.right.BCPressure.Cycle                     "constant"
pfset Patch.right.BCPressure.alltime.Value             0.0

pfset Patch.front.BCPressure.Type                      FluxConst
pfset Patch.front.BCPressure.Cycle                     "constant"
pfset Patch.front.BCPressure.alltime.Value             0.0

pfset Patch.back.BCPressure.Type                      FluxConst
pfset Patch.back.BCPressure.Cycle                     "constant"
pfset Patch.back.BCPressure.alltime.Value             0.0

pfset Patch.bottom.BCPressure.Type                      FluxConst
pfset Patch.bottom.BCPressure.Cycle                     "constant"
pfset Patch.bottom.BCPressure.alltime.Value             0.00005
# Flux set in m/h
# For given domain dimensions(L=1000m,W=1m) corresponds to
# 0.005 * 1000 = 5 m3/h = 120 m3/d
# For given domain dimensions (L= 1000m, W = 100m) corresponds to
# 0,00005 * 1000 * 100 = 5 m3/h = 120 m3/d

pfset Patch.top.BCPressure.Type                       OverlandFlow
pfset Patch.top.BCPressure.Cycle                      "constant"
pfset Patch.top.BCPressure.alltime.Value              0.0

#---------------------------------------------------------
# Topo slopes in x-direction
#---------------------------------------------------------

pfset TopoSlopesX.Type "Constant"
pfset TopoSlopesX.GeomNames "domain river hillslope"
pfset TopoSlopesX.Geom.domain.Value 0.0
pfset TopoSlopesX.Geom.hillslope.Value 0.03
pfset TopoSlopesX.Geom.river.Value 0.0

#---------------------------------------------------------
# Topo slopes in y-direction
#---------------------------------------------------------

pfset TopoSlopesY.Type "Constant"
pfset TopoSlopesY.GeomNames "domain river hillslope"
pfset TopoSlopesY.Geom.domain.Value 0.0
pfset TopoSlopesY.Geom.hillslope.Value 0.0
pfset TopoSlopesY.Geom.river.Value 0.001

#---------------------------------------------------------
# Mannings coefficient 
#---------------------------------------------------------

pfset Mannings.Type "Constant"
pfset Mannings.GeomNames "domain river hillslope"
#pfset Mannings.Geom.domain.Value 5.52e-5
# Set in hr/(m^(1/3))
# 5.52E-5 * 3600 = 0.20 - this value is too large. It's characteristic of a flooded forest
# Changed the value to 0.03 s/(m^(1/3)) characteristic of a stable channel with coarse sand/gravel bed
pfset Mannings.Geom.domain.Value 8.333e-6
pfset Mannings.Geom.river.Value 8.333e-6
pfset Mannings.Geom.hillslope.Value 5.52E-5

#-----------------------------------------------------------------------------
# Phase sources:
#-----------------------------------------------------------------------------

pfset PhaseSources.water.Type                         Constant
pfset PhaseSources.water.GeomNames                    domain
pfset PhaseSources.water.Geom.domain.Value        0.0

#-----------------------------------------------------------------------------
# Exact solution specification for error calculations
#-----------------------------------------------------------------------------

pfset KnownSolution                                    NoKnownSolution

#-----------------------------------------------------------------------------
# Set solver parameters
#-----------------------------------------------------------------------------
pfset Solver                                             Richards
pfset Solver.MaxIter                                     2500000

pfset Solver.TerrainFollowingGrid                        True

pfset Solver.Nonlinear.MaxIter                           300
pfset Solver.Nonlinear.ResidualTol                       1.0e-8
pfset Solver.Nonlinear.EtaChoice                         Walker1 
pfset Solver.Nonlinear.EtaChoice                         EtaConstant
pfset Solver.Nonlinear.EtaValue                          0.001
pfset Solver.Nonlinear.UseJacobian                       True
pfset Solver.Nonlinear.DerivativeEpsilon                 1e-16
pfset Solver.Nonlinear.StepTol				 1e-10
pfset Solver.Nonlinear.Globalization                     LineSearch
pfset Solver.Linear.KrylovDimension                      40
pfset Solver.Linear.MaxRestart                           2

pfset Solver.Linear.Preconditioner                       PFMG

#pfset Solver.Linear.Preconditioner                       PFMG
#pfset Solver.Linear.Preconditioner.PCMatrixType          FullJacobian

#pfset Solver.Linear.Preconditioner.PCMatrixType     FullJacobian

#pfset Solver.Linear.Preconditioner                       MGSemi
#pfset Solver.Linear.Preconditioner.MGSemi.MaxIter        1
#pfset Solver.Linear.Preconditioner.MGSemi.MaxLevels      100

pfset Solver.Drop                                      1E-20
pfset Solver.AbsTol                                     1E-9

pfset Solver.LSM                                         CLM
pfset Solver.WriteSiloCLM                                False
pfset Solver.CLM.Print1dOut                              True
pfset Solver.BinaryOutDir                                ./binout
pfset Solver.CLM.CLMDumpInterval                         8760

pfset Solver.CLM.MetForcing                              1D
pfset Solver.CLM.MetFileName                             narr_1hr.wet.txt
pfset Solver.CLM.MetFilePath                             ./
pfset Solver.CLM.IstepStart                              1
# Write only one RST file.
pfset Solver.CLM.WriteLastRST      True
pfset Solver.CLM.DailyRST     False     

pfset Solver.PrintPressure                              True
pfset Solver.PrintSaturation                            False
pfset Solver.PrintSubsurfData                           False
pfset Solver.PrintLSMSink                               False
pfset Solver.PrintEvapTransSum                          True
pfset Solver.PrintSlopes                                True
pfset Solver.PrintMannings                              False
pfset Solver.PrintMask                                  False
pfset Solver.PrintOverlandSum                           False

pfset Solver.WriteSiloPressure                          False
pfset Solver.WriteSiloSaturation                        False
pfset Solver.WriteSiloSlopes                            False
pfset Solver.WriteSiloMask                              False
pfset Solver.WriteSiloEvapTrans                         False
pfset Solver.WriteSiloOverlandSum                       False
pfset Solver.WriteSiloMannings                          False

# pfset NetCDF.NumStepsPerFile			17544
# pfset NetCDF.WritePressure			True
# pfset NetCDF.WriteSaturation			True
# pfset NetCDF.WriteMannings			True
# pfset NetCDF.WriteSubsurface			True
# pfset NetCDF.WriteSlopes			True
# pfset NetCDF.WriteMask				True
# pfset NetCDF.WriteDZMultiplier			True
# pfset NetCDF.WriteEvapTrans			True
# pfset NetCDF.WriteEvapTransSum			True
# pfset NetCDF.WriteOverlandSum			True
# pfset NetCDF.WriteOverlandBCFlux		True

#pfset NetCDF.WriteCLM				True
#pfset NetCDF.CLMNumStepsPerFile                 24




#---------------------------------------------------------
# Initial conditions: water pressure
#---------------------------------------------------------

#pfset ICPressure.Type                                   HydroStaticPatch
#pfset ICPressure.GeomNames                              domain
#pfset Geom.domain.ICPressure.Value                      -0.125

#pfset Geom.domain.ICPressure.RefGeom                    domain
#pfset Geom.domain.ICPressure.RefPatch                   top

pfdist press.ini.pfb
pfset ICPressure.Type                                   PFBFile
pfset Geom.domain.ICPressure.FileName                   press.ini.pfb
pfset ICPressure.GeomNames                              domain

#-----------------------------------------------------------------------------
# Run and Unload the ParFlow output files
#-----------------------------------------------------------------------------

#pfrun profile
pfwritedb profile
#pfundist profile
