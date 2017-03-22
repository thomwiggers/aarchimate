from library import Register, start_file, start_function, end_function

start_file()

input_0 = Register('input_0', type='x', register='x0')
t0 = Register('t0', pointer=input_0)
start_function('test', [input_0], [t0])
t0.load()
t1 = Register('t1')
t1.and_(t0, t0)
t0.xor(t0, t1)
t0.store(input_0)
end_function()

start_function('test2', [], [])
end_function()
