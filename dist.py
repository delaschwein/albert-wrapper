with open("friendly_orders.txt", "r") as f:
    friendly = f.readlines()

with open("default_orders.txt", "r") as f:
    defaults = f.readlines()

ff = {}

for f in friendly:
    if f not in ff:
        ff[f] = 0
    ff[f] += 1

df = {}

for d in defaults:
    if d not in df:
        df[d] = 0
    df[d] += 1

sorted_ff = sorted(ff.items(), key=lambda x: x[1], reverse=True)
sorted_df = sorted(df.items(), key=lambda x: x[1], reverse=True)

print("Friendly orders:")
for f in sorted_ff:
    print(f[0].strip(), f[1])

print("\nDefault orders:")
for d in sorted_df:
    print(d[0].strip(), d[1])