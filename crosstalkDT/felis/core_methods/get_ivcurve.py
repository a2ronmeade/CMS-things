from ._shared_imports import *

def get_ivcurve(paths_files, path_results, **kwargs):
  ROOT.gErrorIgnoreLevel = ROOT.kFatal  # Suppress ROOT messages

  module_specs = kwargs.get("module_specs")
  is_sane = True
  AS = {}  # Actionable summary for this test.
  explanation = ""
  message = ""

  I_25 = -999
  I_80 = -999
  I_100 = -999
  I_120 = -999
  minTemp_K = -999
  scaleFactor = -999
  V_breakdown = 999

  # Find the Temperature Monitoring ROOT file
  # Set scale factor to be different from 1 if temperatures found
  scaleFactor = 1.0
  status, path_Monitor = get_file_regex(paths_files, regex=r"(?i).*monitor.*\.root$")

  if status:
    # Find the TGraphs within Monitor ROOT File r"Detector/Board_\d+/OpticalGroup_\d+/Hybrid_\d+/Chip_\d+/D_B(\d+)_O(\d+)_H(\d+)_DQM_INTERNAL_NTC_Chip(\d+)"
    status_Monitor, v_paths_chipCanvases = find_rootPaths(path_Monitor)

    file_monitor = ROOT.TFile(path_Monitor, "READ")

    if status_Monitor:
      # Loop through the TGraphs and find the minimum temperature greater than 0 C
      v_minTemperature = []
      for path_chipCanvases in v_paths_chipCanvases:
        numbers = extract_pathNumbers(path_chipCanvases)
        name_graph = "D_B({})_O({})_H({})_DQM_INTERNAL_NTC_Chip({})".format(*numbers)
        tdirectory = file_monitor.Get(path_chipCanvases)
        g_monitor = tdirectory.Get(name_graph)
        v_temp = g_monitor.GetY()
        min_temp = min((temp for temp in v_temp if temp>-50), default=None)
        v_minTemperature.append(min_temp)
      if min_temp == None: # Protects against empty TGraphs
        minTemp_K = -999
        message += "I-V Curve | No minimum temperatures found in monitor file. "
      else:
        # Find the mean of the minimum temperatures of all the ROCs
        minTemp_K = sum(v_minTemperature)/len(v_minTemperature) + 273.15

        # Find the scale factor due to temperature
        k_B = 8.61733e-5  # Boltzmann constant in eV/K
        T_ref = 293.15  # Reference temperature (20C) in Kelvin
        scaleFactor = (T_ref ** 2 / minTemp_K ** 2) * math.exp((-1.21 / (2 * k_B)) * ((1 / T_ref) - (1 / minTemp_K)))

        message += "I-V Curve | Found temperature monitoring file and calculated scale factor."
    else:
      message += "IV-Curve | Could not find TGraphs within the Monitoring ROOT file"

  else:
    message += "I-V Curve | None or more than one temperature monitoring files were found. Currents not scaled."

  # Divide by the sensor area
  if module_specs["type_module"] == "1x2":
    areaFactor = 7.85  # in cm^2
  elif module_specs["type_module"] == "2x2":
    areaFactor = 15.41  # in cm^2
  else:
    return False, "I-V Curve | Must specify type_module in set_module()", None, None, None

  # Find the Analysis ROOT file
  status, path_Analysis_ROOT = get_file_regex(paths_files)

  if status:
    # Find the TCanvas path within Analysis ROOT File
    status, v_cPath_Analysis = find_rootPaths(path_Analysis_ROOT, pattern = r"Detector/Board_\d+/OpticalGroup_\d+/Hybrid_\d+")
    if not status or len(v_cPath_Analysis) != 1:
      return False, "I-V Curve | Could not find TCanvas within Analysis ROOT File.", None, None, None
    cPath_Analysis = v_cPath_Analysis[0]

    # Find the TGraph of the I-V Curve from the Analysis ROOT file
    # Extract the currents at -25, -80, -100, -120 V
    file_Analysis = ROOT.TFile(path_Analysis_ROOT)

    ROOT.gStyle.SetImageScaling(3.0)
    ROOT.gROOT.SetBatch(True)
    tdirectory = file_Analysis.Get(cPath_Analysis)
    c_IV = tdirectory.Get("c_IV")
    g_IV = c_IV.GetPrimitive("g_IV")
    fit_25 = ROOT.TF1("fit_25", "[0]", 23., 27.)
    fit_80 = ROOT.TF1("fit_80", "[0]", 78., 82.)
    fit_100 = ROOT.TF1("fit_100", "[0]", 98., 102.)
    fit_120 = ROOT.TF1("fit_120", "[0]", 118., 122.)

    g_IV_scaled = g_IV.Clone()
    g_IV_scaled.SetName("g_IV_scaled")
    g_IV_scaled.SetTitle("; Reverse Bias (V); Leakage Current (#muA)")
    g_IV_scaled.Scale(scaleFactor)
    scaleVertical = 1.1*max(scaleFactor, 1)*g_IV_scaled.GetMaximum()
    g_IV_scaled.SetMaximum(scaleVertical)
    g_IV_scaled.SetMinimum(0)
    g_IV_scaled.SetMarkerStyle(22)
    g_IV_scaled.SetMarkerColor(2)

    maxVoltage = max(g_IV_scaled.GetX())
    if maxVoltage > 30:
      g_IV_scaled.Fit(fit_25, "QR")
      I_25 = fit_25.GetParameter(0)
    if maxVoltage > 85:
      g_IV_scaled.Fit(fit_80, "QR+")
      I_80 = fit_80.GetParameter(0)
    if module_specs["type_sensor"] == "planar":
      if maxVoltage > 105:
        g_IV_scaled.Fit(fit_100, "QR+")
        I_100 = fit_100.GetParameter(0)
      if maxVoltage > 125:
        g_IV_scaled.Fit(fit_120, "QR+")
        I_120 = fit_120.GetParameter(0)

    # Find the breakdown voltage above 80 V
    [V_breakdown, I_breakdown, percentChange] = find_breakdown(g_IV_scaled, 80)
    
    # Pretty up the plot for export to Panthera
    latex = ROOT.TLatex()
    latex.SetNDC(); latex.SetTextSize(0.03)
    c_IV = ROOT.TCanvas("c_IV", "c_IV", 800, 800)
    g_IV_scaled.Draw("AP")
    g_IV.Draw("P")
    if module_specs["type_sensor"] == "planar":
      # latex.DrawLatex(0.47, 0.85, f"I(100 V) = {I_100:1.3f} #muA")
      latex.DrawLatex(0.47, 0.85, f"I(120 V) = {I_120:1.3f} #muA")
    elif module_specs["type_sensor"] == "3D":
      latex.DrawLatex(0.47, 0.85, f"I(25 V) = {I_25:1.3f} #muA")
      latex.DrawLatex(0.47, 0.82, f"I(80 V) = {I_80:1.3f} #muA")
    if V_breakdown == 999:
      latex.DrawLatex(0.47, 0.79, f"Breakdown Voltage > {maxVoltage:1.0} V")
    else:
      latex.DrawLatex(0.47, 0.79, f"Breakdown Voltage = {V_breakdown:1.0f} V")
    legend = ROOT.TLegend(.12, .88, .42, .75)
    legend.AddEntry(g_IV, "Measured Current")
    if minTemp_K != -999:
      latex.DrawLatex(0.47, 0.76,  f"Scale Factor = {scaleFactor:1.2f}")
      latex.DrawLatex(0.47, 0.73,  f"Min Temp = {(minTemp_K - 273.15):1.2f}#circC")
      legend.AddEntry(g_IV_scaled, "Scaled to 20#circC")
    else:
      latex.DrawLatex(0.47, 0.70,  "No temperature monitor data")
    legend.SetLineColor(0)
    legend.SetFillColor(0)
    legend.Draw()
    c_IV.Update()

    # Draw a secondary axis on the right with area-unscaled current
    pad_xmin = c_IV.GetUxmin(); pad_xmax = c_IV.GetUxmax()
    pad_ymin = c_IV.GetUymin(); pad_ymax = c_IV.GetUymax()
    ymin = pad_ymin / areaFactor
    ymax = pad_ymax / areaFactor
    axis_right = ROOT.TGaxis(pad_xmax, pad_ymin, pad_xmax, pad_ymax, ymin, ymax, 510, "+L")
    axis_right.SetLabelFont(42)
    axis_right.SetLabelSize(0.035)
    axis_right.SetTitle("Leakage Current per Area (#muA/cm^{2})")
    axis_right.SetTitleFont(42)
    axis_right.Draw()
    
    export_canvas(c_IV, "c_IV", path_results)

    # Make and save a canvas without the temperature scaling
    c_IV_unscaled = ROOT.TCanvas("c_IV_unscaled", "c_IV_unscaled", 800, 800)
    g_IV.Draw("AP")
    g_IV.SetMaximum(1.1*g_IV.GetMaximum())
    latex_unscaled = ROOT.TLatex()
    latex_unscaled.SetNDC(); latex_unscaled.SetTextSize(0.03)
    if module_specs["type_sensor"] == "planar":
    #  latex_unscaled.DrawLatex(0.47, 0.85, f"I(100 V) = {I_100/scaleFactor:1.3f} #muA"+f" #rightarrow {I_100*1e3/(areaFactor*scaleFactor):1.1f}"+" nA/cm^{2}")
      latex_unscaled.DrawLatex(0.47, 0.85, f"I(120 V) = {I_120/scaleFactor:1.3f} #muA"+f" #rightarrow {I_120*1e3/(areaFactor*scaleFactor):1.1f}"+" nA/cm^{2}")
    elif module_specs["type_sensor"] == "3D":
      latex_unscaled.DrawLatex(0.47, 0.85, f"I(25 V) = {I_25/scaleFactor:1.3f} #muA"+f" #rightarrow {I_25*1e3/(areaFactor*scaleFactor):1.1f}"+" nA/cm^{2}")
      latex_unscaled.DrawLatex(0.47, 0.82, f"I(80 V) = {I_80/scaleFactor:1.3f} #muA"+f" #rightarrow {I_80*1e3/(areaFactor*scaleFactor):1.1f}"+" nA/cm^{2}")
    if V_breakdown == 999:
      latex_unscaled.DrawLatex(0.47, 0.79, f"Breakdown Voltage > {maxVoltage:1.0} V")
    else:
      latex_unscaled.DrawLatex(0.47, 0.79, f"Breakdown Voltage = {V_breakdown:1.0f} V")
    legend = ROOT.TLegend(.12, .88, .42, .75)
    legend.AddEntry(g_IV, "Measured Current")
    legend.SetLineColor(0)
    legend.SetFillColor(0)
    legend.Draw()
    c_IV_unscaled.Update()
    export_canvas(c_IV_unscaled, "c_IV_unscaled", path_results)

    message += "I-V Curve | Found Analysis ROOT File, extracted sample currents and breakdown voltage."
  else:
    return False, "I-V Curve | None or more than one Analysis ROOT file found.", None, None, None

  AS[key_AS["ivcurve"][0]] = minTemp_K
  AS[key_AS["ivcurve"][1]] = I_25
  AS[key_AS["ivcurve"][2]] = I_80
  AS[key_AS["ivcurve"][3]] = I_100
  AS[key_AS["ivcurve"][4]] = I_120
  AS[key_AS["ivcurve"][5]] = V_breakdown

  # Commenting out sanity check till we understand valid ranges
  '''
  if not in_range(I_25, ivcurve_I_limits):
    is_sane = False
    explanation += explanation_template.format("IVCURVE_I_25", I_20, ivcurve_I_limits)

  if not in_range(I_100, ivcurve_I_limits):
    is_sane = False
    explanation += explanation_template.format("IVCURVE_I_100", I_100, ivcurve_I_limits)
  '''
  
  return status, message, AS, is_sane, explanation

def find_breakdown(g, V_min):
  g_clone = g.Clone()
  g_clone.Sort()

  n = g_clone.GetN()
  v_x = g_clone.GetX()
  v_y = g_clone.GetY()

  for i in range(1, n-1):
    if v_x[i] > V_min:
      dx = 0.5*((v_x[i]+v_x[i+1]) - (v_x[i-1]+v_x[i-2]))
      if dx == 0:
        continue
      slope = 0.5*((v_y[i]+v_y[i+1]) - (v_y[i-1]+v_y[i-2]))/dx
      percentChange = slope*5/v_y[i]
      if percentChange > 0.2 and percentChange < 0.35:
        V_breakdown = v_x[i]
        return [v_x[i], v_y[i], percentChange]

  return [999, 999, -1]
