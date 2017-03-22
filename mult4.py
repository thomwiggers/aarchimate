from library import (
    start_file, Register, start_function, end_function, do_and, do_xor)

# based on https://binary.cr.yp.to/m.html

start_file()

h_pointer = Register('h', type='x', register='x0')
h0 = Register('h0', pointer=h_pointer, offset=0)
h1 = Register('h1', pointer=h_pointer, offset=4)
h2 = Register('h2', pointer=h_pointer, offset=8)
h3 = Register('h3', pointer=h_pointer, offset=12)
h4 = Register('h4', pointer=h_pointer, offset=16)
h5 = Register('h5', pointer=h_pointer, offset=20)
h6 = Register('h6', pointer=h_pointer, offset=24)

f_pointer = Register('f', type='x', register='x1')
f0 = Register('f0', pointer=h_pointer, offset=0)
f1 = Register('f1', pointer=h_pointer, offset=4)
f2 = Register('f2', pointer=h_pointer, offset=8)
f3 = Register('f3', pointer=h_pointer, offset=12)

g_pointer = Register('g', type='x', register='x2')
g0 = Register('g0', pointer=h_pointer, offset=0)
g1 = Register('g1', pointer=h_pointer, offset=4)
g2 = Register('g2', pointer=h_pointer, offset=8)
g3 = Register('g3', pointer=h_pointer, offset=12)

start_function('mult4', [h_pointer, f_pointer, g_pointer],
               [f0, f1, f2, f3, g0, g1, g2, g3])
f3.load()
g3.load()
g0.load()
h0.and_(f3, g3)
t1 = h0
g1.load()
t2 = do_and('t2', f3, g0)
g2.load()
f0.load()
t4 = do_and('t4', f3, g2)
f1.load()
t5 = do_and('t5', f0, g3)
f2.load()
t6 = do_and('t6', f1, g3)
h0.store()
t7 = do_and('t7', f2, g3)
t8 = do_and('t8', f2, g2)
t25 = do_xor('t25', t7, t4)
t7.unload()
t4.unload()
t9 = do_and('t9', f2, g0)
h5.store_from(t25)
t25.unload()
t22 = do_xor('t22', t8, t6)
t8.unload()
t6.unload()
t10 = do_and('t10', f2, g1)
f2.unload()
t11 = do_and('t11', f0, g2)
t12 = do_and('t12', f1, g2)
g2.unload()
t13 = do_and('t13', f1, g1)
t14 = do_and('t14', f1, g0)
t20 = do_xor('t20', t12, t10)
t12.unload()
t10.unload()
f1.unload()
t15 = do_and('t15', f0, g1)
t16 = do_and('t16', f0, g0)
f0.unload()
g0.unload()
t18 = do_xor('t18', t13, t11)
h0.store_from(t16)
t19 = do_xor('t19', t18, t9)
t21 = do_xor('t21', t20, t5)
t17 = do_xor('t17', t15, t14)
t23 = do_xor('t23', t21, t2)
h2.store_from(t19)
t3 = do_and('t3', f3, g1)
t16.unload()
h3.store_from(t23)
t24 = do_xor('t24', t22, t3)
h1.store_from(t17)
t17.unload()
h4.store_from(t24)

end_function()
