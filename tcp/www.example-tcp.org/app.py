from flask import Flask, render_template
app = Flask(__name__, static_url_path="", static_folder="static")

@app.route('/')
def index():
        return 'Hello Flask/Apache'

@app.route('/5k.html')
def resource_5k():
        return render_template('5k.html')

@app.route('/5kx200.html')
def resource_5kx200():
        return render_template('5kx200.html', n=200)

@app.route('/10k.html')
def resource_10k():
        return render_template('10k.html')

@app.route('/10kx100.html')
def resource_10kx100():
        return render_template('10kx100.html', n=100)

@app.route('/100k.html')
def resource_100k():
        return render_template('100k.html')

@app.route('/100kx10.html')
def resource_100kx10():
        return render_template('100kx10.html', n=10)

@app.route('/200k.html')
def resource_200k():
        return render_template('200k.html')

@app.route('/200kx5.html')
def resource_200kx5():
        return render_template('200kx5.html', n=5)

@app.route('/500k.html')
def resource_500k():
        return render_template('500k.html')

@app.route('/500kx2.html')
def resource_500kx2():
        return render_template('500kx2.html', n=2)

@app.route('/1mb.html')
def resource_1mb():
        return render_template('1mb.html')

@app.route('/1mbx1.html')
def resource_1mbx1():
        return render_template('1mbx1.html', n=1)

@app.route('/10mb.html')
def resource_10mb():
        return render_template('10mb.html')

