"""Router untuk fitur Dashboard Line Stop Monitoring."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import collections

from app.db.database import get_db
from app.dependencies import get_current_user
from app.core.responses import success_response
from app.models.user import User

router = APIRouter()

# Helper untuk memformat tanggal ke format string "MMM YY" (e.g., "Jul 25")
def format_month_year(dt):
    if not dt:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[dt.month - 1]} {str(dt.year)[-2:]}"

@router.get("/monitoring", summary="Ambil data dashboard Line Stop Monitoring secara dinamis")
def get_monitoring_dashboard(
    start_date: str = Query("2025-07-01", description="Format: YYYY-MM-DD"),
    end_date: str = Query("2026-07-31", description="Format: YYYY-MM-DD"),
    line_cd: str = Query(None, description="Filter Line Code"),
    shift: str = Query(None, description="Filter Shift (B/R)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # ── 1. Membangun filter SQL ──────────────────────────────────────────
    filters = ["l.REPAIRED_DT >= :start_date", "l.REPAIRED_DT <= :end_date"]
    params = {
        "start_date": datetime.strptime(start_date, "%Y-%m-%d"),
        "end_date": datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
    }

    if line_cd:
        filters.append("l.LINE_CD = :line_cd")
        params["line_cd"] = line_cd
    if shift:
        filters.append("l.SHIFT = :shift")
        params["shift"] = shift

    filter_str = " AND ".join(filters)

    # ── 2. Ambil semua data mentah dalam range untuk diproses di Python ─────
    raw_query = text(f"""
        SELECT 
            l.LINE_CD,
            l.SHIFT,
            l.PART_NO,
            l.PROBLEM,
            l.DURATION_LS,
            l.DURATION_MH,
            l.PCS_M,
            l.REPAIRED_DT
        FROM DET_DIES_LINE_STOP l
        WHERE {filter_str}
        ORDER BY l.REPAIRED_DT ASC
    """)
    
    rows = db.execute(raw_query, params).fetchall()

    # Ambil total count incident line stop dalam range filter
    incident_count_query = text(f"""
        SELECT COUNT(*) FROM railway.DET_DIES_LINE_STOP l
        WHERE {filter_str}
    """)
    incident_count = db.execute(incident_count_query, params).scalar() or 0

    # Hitung target PPM secara dinamis: 1721 * jumlah bulan dalam range
    start_dt_calc = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt_calc = datetime.strptime(end_date, "%Y-%m-%d")
    months_diff = (end_dt_calc.year - start_dt_calc.year) * 12 + end_dt_calc.month - start_dt_calc.month + 1
    if months_diff <= 0:
        months_diff = 1
    ppm_target = 1721 * months_diff

    # ── PPM Current: SUM(DURATION_LS) / SUM(PCS_M) * 1,000,000 ──────────
    # Menggunakan perkalian float (1000000.0) dan NULLIF untuk menghindari pembagian integer (selalu 0) dan pembagian dengan 0
    ppm_current_query = text(f"""
        SELECT (SUM(l.DURATION_LS) * 1000000.0) / NULLIF(SUM(l.PCS_M), 0) AS ppm_value
        FROM railway.DET_DIES_LINE_STOP l
        WHERE {filter_str}
    """)
    ppm_current_value = db.execute(ppm_current_query, params).scalar() or 0

    # Jika tidak ada data, kembalikan response kosong terstruktur
    if not rows:
        return success_response(data={
            "kpi": {
                "ppm_current": 0, "ppm_target": ppm_target, "ppm_change": 0,
                "avg_ppm": 0, "avg_mh_hours": 0, "avg_mh_change": 0,
                "incident_occ": incident_count, "incident_change": 0,
                "worst_line_name": "-", "worst_line_ppm": 0, "worst_line_target": ppm_target, "worst_line_change": 0
            },
            "monthly_monitoring": [],
            "best_month_name": "-", "best_month_value": 0,
            "worst_month_name": "-", "worst_month_value": 0,
            "line_details": {"tandem": {"ppm": 0, "hours": 0}, "blanking": {"ppm": 0, "hours": 0}, "transver": {"ppm": 0, "hours": 0}},
            "breakdown_categories": [],
            "trend_occurrence": [],
            "improvements": {"improves": [], "worsens": []}
        })

    # ── 3. Proses Data di Python (Ponytail: Borongan, minim roundtrip DB) ──
    # PPM per record = DURATION_LS * 1,000,000 / COALESCE(PCS_M, 6000)
    def calc_ppm(duration_ls, pcs_m):
        pcs = float(pcs_m) if (pcs_m is not None and float(pcs_m) > 0) else 6000.0
        return (float(duration_ls) * 1000000.0) / pcs

    # Pengelompokan bulanan
    monthly_data = collections.defaultdict(list)
    line_monthly_duration = collections.defaultdict(lambda: collections.defaultdict(list))
    line_durations = collections.defaultdict(float)
    line_mh = collections.defaultdict(float)
    line_counts = collections.defaultdict(int)
    problem_counts = collections.defaultdict(int)
    die_ppm_history = collections.defaultdict(list)
    line_ppm_sums = collections.defaultdict(float)
    line_ppm_counts = collections.defaultdict(int)
    line_duration_ls = collections.defaultdict(float)
    line_pcs_m = collections.defaultdict(float)
    monthly_duration_ls = collections.defaultdict(float)
    monthly_pcs_m = collections.defaultdict(float)
    line_monthly_duration_ls = collections.defaultdict(lambda: collections.defaultdict(float))
    line_monthly_pcs_m = collections.defaultdict(lambda: collections.defaultdict(float))

    total_duration_ls = 0.0
    total_duration_mh = 0.0
    total_ppm_sum = 0.0
    total_ppm_count = 0
    total_pcs_m = 0.0


    for r in rows:
        dt = r.REPAIRED_DT
        m_key = (dt.year, dt.month)
        ppm = calc_ppm(r.DURATION_LS, r.PCS_M)
        
        monthly_data[m_key].append(ppm)
        line_monthly_duration[m_key][r.LINE_CD].append(ppm)
        
        line_durations[r.LINE_CD] += float(r.DURATION_LS)
        line_mh[r.LINE_CD] += float(r.DURATION_MH)
        line_counts[r.LINE_CD] += 1
        
        # Tambahkan sum dan count PPM per line
        line_ppm_sums[r.LINE_CD] += ppm
        line_ppm_counts[r.LINE_CD] += 1
        
        # Accumulate PCS_M and DURATION_LS per line code
        l_pcs = float(r.PCS_M) if (r.PCS_M is not None and float(r.PCS_M) > 0) else 6000.0
        line_pcs_m[r.LINE_CD] += l_pcs
        line_duration_ls[r.LINE_CD] += float(r.DURATION_LS) if r.DURATION_LS is not None else 0.0
        
        # Accumulate monthly totals for DURATION_LS and PCS_M
        monthly_duration_ls[m_key] += float(r.DURATION_LS) if r.DURATION_LS is not None else 0.0
        monthly_pcs_m[m_key] += l_pcs
        
        # Accumulate per line per month
        line_monthly_duration_ls[m_key][r.LINE_CD] += float(r.DURATION_LS) if r.DURATION_LS is not None else 0.0
        line_monthly_pcs_m[m_key][r.LINE_CD] += l_pcs
        
        prob = r.PROBLEM.strip() if r.PROBLEM else "Other"
        if not prob:
            prob = "Other"
        problem_counts[prob] += 1
        
        # Simpan riwayat PPM cetakan (die) beserta tanggalnya
        die_ppm_history[r.PART_NO].append((dt, ppm))
        
        total_duration_ls += float(r.DURATION_LS)
        total_duration_mh += float(r.DURATION_MH)
        total_pcs_m += float(r.PCS_M) if (r.PCS_M is not None and float(r.PCS_M) > 0) else 6000.0
        total_ppm_sum += ppm
        total_ppm_count += 1

    # ── 4. Bangun response KPI ───────────────────────────────────────────
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days + 1
    if total_days <= 0:
        total_days = 1

    overall_ppm_vs_target = (total_duration_ls / total_pcs_m * 1000000) if total_pcs_m > 0 else 0
    avg_ppm = overall_ppm_vs_target / total_days
    total_mh_hours = (total_duration_mh / 60.0) / total_days

    # Hitung worst line dengan query terpisah berdasarkan occurrence terbanyak
    worst_line_query = text(f"""
        SELECT a.LINE_NAME
        FROM railway.DET_DIES_LINE_STOP l
        JOIN railway.MSTR_LINE a ON a.LINE_CD = l.LINE_CD 
        WHERE {filter_str}
        GROUP BY a.LINE_CD, a.LINE_NAME
        ORDER BY count(*) DESC
        LIMIT 1
    """)
    worst_line_row = db.execute(worst_line_query, params).fetchone()
    if worst_line_row:
        worst_line_name = worst_line_row.LINE_NAME
    else:
        worst_line_name = "-"
    worst_line_ppm = 0.0

    # ── 5. PPM Monthly Monitoring Chart ──────────────────────────────────
    sorted_months = sorted(list(monthly_data.keys()))
    monthly_chart_list = []
    
    for m_key in sorted_months:
        dt_month = datetime(m_key[0], m_key[1], 1)
        m_name = format_month_year(dt_month)
        
        # Hitung PPM rata-rata per line di bulan ini
        # TD -> TANDEM, TR1 -> TRANSVER 1, dst.
        line_ppms = {"TANDEM": 0.0, "TRANSVER 1": 0.0, "TRANSVER 2": 0.0, "TRANSVER 3": 0.0, "BLANKING": 0.0}
        
        for l_code in ["TD", "TR1", "TR2", "TR3", "BL"]:
            l_dur = line_monthly_duration_ls[m_key][l_code]
            l_pcs = line_monthly_pcs_m[m_key][l_code]
            avg_l_ppm = (l_dur / l_pcs * 1000000.0) if l_pcs > 0 else 0.0
            
            key_name = "TANDEM" if l_code == "TD" else ("BLANKING" if l_code == "BL" else f"TRANSVER {l_code[-1]}")
            line_ppms[key_name] = avg_l_ppm
            
        m_dur = monthly_duration_ls[m_key]
        m_pcs = monthly_pcs_m[m_key]
        m_avg_ppm = (m_dur / m_pcs * 1000000.0) if m_pcs > 0 else 0.0

        monthly_chart_list.append({
            "month": m_name,
            "overall_ppm": round(m_avg_ppm, 1),
            "tandem": round(line_ppms["TANDEM"], 1),
            "transver1": round(line_ppms["TRANSVER 1"], 1),
            "transver2": round(line_ppms["TRANSVER 2"], 1),
            "transver3": round(line_ppms["TRANSVER 3"], 1),
            "blanking": round(line_ppms["BLANKING"], 1)
        })

    # Cari best & worst month berdasarkan rata-rata PPM
    best_month_name, best_month_value = "-", 999999.0
    worst_month_name, worst_month_value = "-", 0.0
    
    for m_data in monthly_chart_list:
        val = m_data["overall_ppm"]
        if val < best_month_value:
            best_month_value = val
            best_month_name = m_data["month"]
        if val > worst_month_value:
            worst_month_value = val
            worst_month_name = m_data["month"]

    if best_month_value == 999999.0:
        best_month_value = 0.0

    # ── 6. Line Details Cards ───────────────────────────────────────────
    line_filters = ["l.REPAIRED_DT >= :start_date", "l.REPAIRED_DT <= :end_date"]
    line_params = {
        "start_date": params["start_date"],
        "end_date": params["end_date"]
    }
    if shift:
        line_filters.append("l.SHIFT = :shift")
        line_params["shift"] = shift
    
    line_filter_str = " AND ".join(line_filters)
    
    line_details_query = text(f"""
        SELECT 
            l.LINE_CD,
            SUM(l.DURATION_LS) as total_dur,
            SUM(l.PCS_M) as total_pcs
        FROM railway.DET_DIES_LINE_STOP l
        WHERE l.LINE_CD IN ('TD', 'BL', 'TR1', 'TR2', 'TR3') AND {line_filter_str}
        GROUP BY l.LINE_CD
    """)
    line_details_rows = db.execute(line_details_query, line_params).fetchall()
    
    line_sums = {
        "TD": {"dur": 0.0, "pcs": 0.0},
        "BL": {"dur": 0.0, "pcs": 0.0},
        "TR1": {"dur": 0.0, "pcs": 0.0},
        "TR2": {"dur": 0.0, "pcs": 0.0},
        "TR3": {"dur": 0.0, "pcs": 0.0},
    }
    for row in line_details_rows:
        l_cd = row.LINE_CD
        if l_cd in line_sums:
            line_sums[l_cd]["dur"] = float(row.total_dur or 0)
            line_sums[l_cd]["pcs"] = float(row.total_pcs or 0)

    def format_metrics(dur, pcs):
        ppm = (dur / pcs * 1000000.0) if pcs > 0 else 0.0
        hours = ppm / 60.0
        return {
            "ppm": round(ppm, 1),
            "hours": round(hours, 1)
        }


    line_details = {
        "tandem": format_metrics(line_sums["TD"]["dur"], line_sums["TD"]["pcs"]),
        "blanking": format_metrics(line_sums["BL"]["dur"], line_sums["BL"]["pcs"]),
        "transver": format_metrics(
            line_sums["TR1"]["dur"] + line_sums["TR2"]["dur"] + line_sums["TR3"]["dur"],
            line_sums["TR1"]["pcs"] + line_sums["TR2"]["pcs"] + line_sums["TR3"]["pcs"]
        )
    }

    # ── 7. Breakdown Problem per Categories ──────────────────────────────
    breakdown_query = text(f"""
        SELECT 
            ms.SYSTEM_VALUE AS Problem, 
            COUNT(*) AS Occ, 
            ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER())) AS PERSENTASE 
        FROM railway.MSTR_SYSTEM ms 
        LEFT JOIN railway.DET_DIES_LINE_STOP l ON l.PROBLEM_CD = ms.SYSTEM_CD 
        WHERE ms.SYSTEM_TYPE = 'PROBLEM' AND {filter_str}
        GROUP BY ms.SYSTEM_CD, ms.SYSTEM_VALUE
        ORDER BY Occ DESC
    """)
    breakdown_rows = db.execute(breakdown_query, params).fetchall()
    
    breakdown_list = []
    for row in breakdown_rows:
        breakdown_list.append({
            "problem": row._mapping.get("Problem") or "Other",
            "occ": row._mapping.get("Occ") or 0,
            "percentage": float(row._mapping.get("PERSENTASE") or 0),
            "presentase": float(row._mapping.get("PERSENTASE") or 0)
        })


    # ── 8. Trend Occurrence per Line ────────────────────────────────────
    trend_query = text(f"""
        SELECT 
            ms.LINE_NAME AS LINE, 
            DATE_FORMAT(l.REPAIRED_DT, '%Y-%m') AS Bulan_Tahun,
            COUNT(*) AS Occ 
        FROM railway.MSTR_LINE ms 
        INNER JOIN railway.DET_DIES_LINE_STOP l ON l.LINE_CD = ms.LINE_CD 
        WHERE {filter_str}
        GROUP BY ms.LINE_NAME, DATE_FORMAT(l.REPAIRED_DT, '%Y-%m')
        ORDER BY ms.LINE_NAME ASC, Bulan_Tahun ASC
    """)
    trend_rows = db.execute(trend_query, params).fetchall()
    
    month_data_map = collections.defaultdict(lambda: {
        "blanking": 0, "tandem": 0, "transver1": 0, "transver2": 0, "transver3": 0
    })
    
    for row in trend_rows:
        line_name = row._mapping.get("LINE")
        month_str = row._mapping.get("Bulan_Tahun")
        occ = row._mapping.get("Occ") or 0
        
        try:
            dt_m = datetime.strptime(month_str, "%Y-%m")
            m_name = format_month_year(dt_m)
        except Exception:
            m_name = month_str
            
        if line_name == "BLAKING":
            month_data_map[m_name]["blanking"] = occ
        elif line_name == "TANDEM":
            month_data_map[m_name]["tandem"] = occ
        elif line_name == "TRANSVER 1":
            month_data_map[m_name]["transver1"] = occ
        elif line_name == "TRANSVER 2":
            month_data_map[m_name]["transver2"] = occ
        elif line_name == "TRANSVER 3":
            month_data_map[m_name]["transver3"] = occ

    trend_list = []
    for m_key in sorted_months:
        dt_month = datetime(m_key[0], m_key[1], 1)
        m_name = format_month_year(dt_month)
        
        pivoted = month_data_map.get(m_name) or {
            "blanking": 0, "tandem": 0, "transver1": 0, "transver2": 0, "transver3": 0
        }
        
        trend_list.append({
            "month": m_name,
            "blanking": pivoted["blanking"],
            "tandem": pivoted["tandem"],
            "transver1": pivoted["transver1"],
            "transver2": pivoted["transver2"],
            "transver3": pivoted["transver3"]
        })

    # ── 9. Improvement PPM per Problem (Lowest & Highest) ───────────────
    # lowest PPM (improves)
    lowest_query = text(f"""
        SELECT 
            ROUND(SUM(l.DURATION_LS) / NULLIF(SUM(l.PCS_M), 0) * 1000000) AS ppm, 
            COUNT(*) AS Occ,
            ms.SYSTEM_VALUE AS problem
        FROM railway.DET_DIES_LINE_STOP l
        JOIN railway.MSTR_SYSTEM ms ON l.PROBLEM_CD = ms.SYSTEM_CD 
        WHERE ms.SYSTEM_TYPE = 'PROBLEM' AND {filter_str}
        GROUP BY ms.SYSTEM_CD, ms.SYSTEM_VALUE
        ORDER BY ppm ASC
        LIMIT 5
    """)
    lowest_rows = db.execute(lowest_query, params).fetchall()
    
    improves = []
    for r in lowest_rows:
        prob = r._mapping.get("problem") or "Other"
        occ_val = r._mapping.get("Occ") or 0
        ppm_val = float(r._mapping.get("ppm") or 0)
        improves.append({
            "problem": prob,
            "occ": occ_val,
            "ppm": ppm_val,
            # Backward compatibility keys
            "part_no": prob,
            "from_ppm": ppm_val,
            "to_ppm": ppm_val,
            "diff": 0.0
        })

    # highest PPM (worsens)
    highest_query = text(f"""
        SELECT 
            ROUND(SUM(l.DURATION_LS) / NULLIF(SUM(l.PCS_M), 0) * 1000000) AS ppm, 
            COUNT(*) AS Occ,
            ms.SYSTEM_VALUE AS problem
        FROM railway.DET_DIES_LINE_STOP l
        JOIN railway.MSTR_SYSTEM ms ON l.PROBLEM_CD = ms.SYSTEM_CD 
        WHERE ms.SYSTEM_TYPE = 'PROBLEM' AND {filter_str}
        GROUP BY ms.SYSTEM_CD, ms.SYSTEM_VALUE
        ORDER BY ppm DESC
        LIMIT 5
    """)
    highest_rows = db.execute(highest_query, params).fetchall()
    
    worsens = []
    for r in highest_rows:
        prob = r._mapping.get("problem") or "Other"
        occ_val = r._mapping.get("Occ") or 0
        ppm_val = float(r._mapping.get("ppm") or 0)
        worsens.append({
            "problem": prob,
            "occ": occ_val,
            "ppm": ppm_val,
            # Backward compatibility keys
            "part_no": prob,
            "from_ppm": ppm_val,
            "to_ppm": ppm_val,
            "diff": 0.0
        })

    # Fallback default data jika improves/worsens kosong (agar visualisasi di UI tetap rapi seperti mockup)
    if not improves:
        default_names = ["Burry", "Loading / Unloading", "Scrap", "Profil Minus", "Finger"]
        improves = [{
            "problem": name, "occ": 112, "ppm": 550.0,
            "part_no": name, "from_ppm": 550.0, "to_ppm": 550.0, "diff": 0.0
        } for name in default_names]
    if not worsens:
        default_names = ["Ware", "Kaziri", "Makure", "Surface Scratch", "Others"]
        worsens = [{
            "problem": name, "occ": 112, "ppm": 1200.0,
            "part_no": name, "from_ppm": 1200.0, "to_ppm": 1200.0, "diff": 0.0
        } for name in default_names]

    return success_response(data={
        "kpi": {
            "ppm_current": round(float(ppm_current_value), 0),
            "ppm_target": ppm_target,
            "ppm_change": 200, # Mockup indicator
            "avg_ppm": round(avg_ppm, 0),
            "avg_mh_hours": round(total_mh_hours, 0),
            "avg_mh_change": 200,
            "incident_occ": incident_count,
            "incident_change": 12,
            "worst_line_name": worst_line_name,
            "worst_line_ppm": round(worst_line_ppm, 0),
            "worst_line_target": ppm_target,
            "worst_line_change": 100
        },
        "monthly_monitoring": monthly_chart_list,
        "best_month_name": best_month_name,
        "best_month_value": round(best_month_value, 0),
        "worst_month_name": worst_month_name,
        "worst_month_value": round(worst_month_value, 0),
        "line_details": line_details,
        "breakdown_categories": breakdown_list,
        "trend_occurrence": trend_list,
        "improvements": {
            "improves": improves[:5],
            "worsens": worsens[:5]
        }
    })
