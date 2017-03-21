from library import Register, start_file, start_function, end_function

start_file()

input_0 = Register('input_0', type='x', register='x0')
t0 = Register('t0', pointer=input_0)
start_function('test', [input_0], [t0])
t0.load()
end_function()
