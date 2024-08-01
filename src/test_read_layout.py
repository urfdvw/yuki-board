with open("layout.csv") as file:
    raw = file.read().replace('\r', '').strip()
lines = raw.split('\n')
layout_macros = [
    [
        macro.strip()
        for macro in line.strip().split('\t')
    ]
    for line in lines
]
print(layout_macros)

#%%
def mod_range(number, start=-1, end=2):
    while number >= end:
        number -= end - start
    while number < start:
        number += end - start
    return number
    
#%%
def swipe_to_alter(start, end):
    diff = end - start
    alter_x = mod_range(diff % 3, start=-1, end=2)
    alter_y = mod_range(diff // 3, start=-1, end=3)
    return (alter_x, alter_y)
    
#%% test swipe_to_alter

for start, end in (
    (1, 1),
    (1, 2),
    (1, 10),
    (1, 12),
    (1, 6),
    (1, 7)
):
    print(swipe_to_alter(start, end))
    
#%%
def start_to_macro_index(start):
    x = (start - 1) % 3
    y = (start - 1) // 3
    x = x * 3 + 1
    y = y * 3 + 1
    return x, y
    
#%% test

for start in range(1, 13):
    print(start_to_macro_index(start))
    
#%%
def get_macro(start, end):
    alter_x, alter_y = swipe_to_alter(start, end)
    x, y = start_to_macro_index(start)
    x += alter_x
    y += alter_y
    if abs(alter_y) <= 1:
        return layout_macros[y][x]
    else:
        return ""
    
    
#%% over all test
for start, end in (
    (1, 1),
    (1, 2),
    (1, 10),
    (1, 12),
    (1, 6),
    (1, 7)
):
    print(get_macro(start, end))