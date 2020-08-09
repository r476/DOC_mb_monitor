import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import random
import dash_daq as daq
from modbus.client import *

external_stylesheets = ['main.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def get_data():
    data_dict = {}
    try:
        c = client(host="192.168.127.254", unit=7)

        gensets = c.read(FC=3, ADR=287, LEN=5)
        mains_import = c.read(FC=3, ADR=231, LEN=1)[0]
        object_p = c.read(FC=3, ADR=272, LEN=2)[1]
        mwh = c.read(FC=3, ADR=283, LEN=2)[1]
        tot_run_p_act = c.read(FC=3, ADR=339, LEN=2)[1]
        b_in = c.read(FC=3, ADR=2, LEN=1)[0]
        data_dict = {'Дата Время': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     'ГПГУ 1 ': number_sing(gensets[0]),
                     'ГПГУ 2 ': number_sing(gensets[1]),
                     'ГПГУ 3 ': number_sing(gensets[2]),
                     'ГПГУ 4 ': number_sing(gensets[3]),
                     'ГПГУ 5 ': number_sing(gensets[4]),
                     'MainsImport': number_sing(mains_import),
                     'Мощность завода': number_sing(object_p),
                     'MWh': mwh,
                     'Сумм мощность ГПГУ': number_sing(tot_run_p_act),
                     'BIN': b_in}
    except Exception as e:
        print('Неудачная попытка опроса IM.')
        syslog_to_csv(e)
    return data_dict


app.layout = html.Div([
    daq.Gauge(
        id='power',
        color={"gradient": True, "ranges": {"green": [0, 5999], "yellow": [6000, 6499], "red": [6500, 7000]}},
        label='Мощность завода',
        max=7000,
        min=0,
    ),
    dcc.Interval(
                id='interval-component',
                interval=1*1000, # in milliseconds
                n_intervals=0
            )
])

@app.callback(
    Output('power', 'value'),
    [Input('interval-component', 'n_intervals')]
)
def update_val(n):
    return get_data['Мощность завода']

if __name__ == '__main__':
    app.run_server(debug=True)