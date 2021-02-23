from filter import Filter

filter = Filter(0.1)
print(filter.f.P)

for i in range(100):
    filter.predict([-0.4, 0.2, 50])

print(filter.f.x)