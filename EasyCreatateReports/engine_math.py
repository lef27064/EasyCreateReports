import math

SAFE_MATH_DICT = {
    "log": math.log, "exp": math.exp, "sqrt": math.sqrt,
    "abs": abs, "sin": math.sin, "cos": math.cos,
    "pi": math.pi, "e": math.e
}

def create_sum_expression(data_env):
    """Δημιουργεί και επιστρέφει τη συνάρτηση sum_expression δεμένη με το περιβάλλον δεδομένων."""
    def sum_expression(table_key, formula_str):
        table_data = data_env.get(table_key, {})
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        
        total = 0.0
        for row in rows:
            try:
                local_env = SAFE_MATH_DICT.copy()
                for h in headers:
                    col_idx = headers.index(h)
                    try:
                        local_env[h] = float(row[col_idx])
                    except (ValueError, TypeError):
                        local_env[h] = 0.0
                
                val = eval(formula_str, {"__builtins__": {}}, local_env)
                total += float(val)
            except Exception:
                continue
        return round(total, 2)
    return sum_expression
