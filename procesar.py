import os, json, glob
import pandas as pd

# Buscar el Excel más reciente en la carpeta data/
archivos = glob.glob('data/*.xlsx') + glob.glob('data/*.xls')
if not archivos:
    print("❌ No se encontró ningún archivo Excel en data/")
    exit(1)

archivo = sorted(archivos)[-1]
print(f"📂 Procesando: {archivo}")

df = pd.read_excel(archivo, header=0)
print(f"✅ Filas leídas: {len(df)}")

# Normalizar fecha
df['Fe.contab.'] = pd.to_datetime(df['Fe.contab.'], errors='coerce').dt.strftime('%Y-%m-%d')

# Detectar columnas flexiblemente
cols = {c.strip().lower(): c for c in df.columns}

def get_col(*names):
    for n in names:
        if n.lower() in cols:
            return cols[n.lower()]
    return None

kFecha   = get_col('fe.contab.', 'fecha', 'date', 'fe contab')
kCliente = get_col('name socio', 'cliente', 'socio', 'cliente nombre')
kEnvase  = get_col('texto breve de material', 'material', 'envase', 'descripcion')
kMov     = get_col('movimiento', 'tipo', 'movement')
kUds     = get_col('unidades', 'units', 'cantidad')
kPmo     = get_col('pmo ?', 'pmo', 'tipo_pmo', 'tipo pmo')
kWeek    = get_col('week', 'semana', 'wk')

faltantes = [n for n, k in [('Fecha',kFecha),('Cliente',kCliente),('Envase',kEnvase),('Movimiento',kMov),('Unidades',kUds)] if not k]
if faltantes:
    print(f"❌ Columnas no encontradas: {faltantes}")
    print(f"   Columnas disponibles: {list(df.columns)}")
    exit(1)

# Calcular semana si no existe
if kWeek:
    df['_week'] = pd.to_numeric(df[kWeek], errors='coerce').fillna(0).astype(int)
else:
    df['_week'] = pd.to_datetime(df[kFecha], errors='coerce').dt.isocalendar().week.astype(int)

# Normalizar PMO
if kPmo:
    df['_pmo'] = df[kPmo].fillna('PMO').astype(str).str.strip()
else:
    df['_pmo'] = 'PMO'

# Construir registros
df['_fecha']   = df[kFecha].astype(str)
df['_cliente'] = df[kCliente].astype(str).str.strip()
df['_envase']  = df[kEnvase].astype(str).str.strip()
df['_mov']     = df[kMov].astype(str).str.strip()
df['_uds']     = pd.to_numeric(df[kUds], errors='coerce').fillna(0).astype(int)

# Normalizar movimiento
df['_mov'] = df['_mov'].apply(lambda x: 'Retorno' if 'retorno' in x.lower() else 'Venta')

# Agrupar por fecha+cliente+envase+movimiento+pmo+semana (suma de unidades)
group_cols = ['_fecha','_cliente','_envase','_mov','_pmo','_week']
agg = df.groupby(group_cols, as_index=False)['_uds'].sum()

records = []
for _, r in agg.iterrows():
    if not r['_fecha'] or r['_fecha'] == 'NaT': continue
    records.append({
        'f': r['_fecha'],
        'c': r['_cliente'],
        'e': r['_envase'],
        'm': r['_mov'],
        'p': r['_pmo'],
        'w': int(r['_week']),
        'u': int(r['_uds'])
    })

output = json.dumps(records, ensure_ascii=False, separators=(',',':'))
with open('data/data.json', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"✅ data.json generado: {len(records)} registros ({len(output)} bytes)")
