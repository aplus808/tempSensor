from bokeh.plotting import figure, output_file, show

output_file("test.html")
p=figure()
xs = [1,2,3,4,5]
ys = [0,2,10,1,4]
p.line(xs, ys, line_width=2)
show(p)