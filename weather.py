import os
import datetime
import requests
import json
import click
import colorama
from colorama import Fore, Back, Style

def print_json(json_block, sort=True, indents=4):
    if type(json_block) is str:
        print(json.dumps(json.loads(json_block), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_block, sort_keys=sort, indent=indents))

    return None

def print_current_weather(location, api_key, units, time, json, query):
    owm_api_url = 'https://api.openweathermap.org/data/2.5/weather'

    query_params = {
        'q': location,
        'appid': api_key,
        'units': units
    }

    response = requests.get(owm_api_url, params=query_params)

    if query:
        print(f"{Fore.YELLOW}api query: {Fore.WHITE}{response.url}")

    if json:
        print(f"{Fore.YELLOW}response json:")
        print_json(response.json())
    else:
        response_code = response.json()['cod']

        if response_code is not 200:
            response_message = response.json()['message']
            print(f"{Fore.RED}error: {Fore.WHITE}({response_code}) {response_message}")
            exit()

        city = response.json()['name']
        #city_id = response.json()['id']

        unix_timestamp = response.json()['dt']
        if time == 'utc':
            weather_time = datetime.datetime.utcfromtimestamp(int(unix_timestamp))
        else:
            weather_time = datetime.datetime.fromtimestamp(int(unix_timestamp))

        weather_time = weather_time.strftime('%Y-%m-%d %H:%M')

        country = response.json()['sys']['country']

        temp = response.json()['main']['temp']

        weather = ""
        for item in response.json()['weather']:
            weather += item['description'] + ", "
        weather = weather[:-2]

        wind = response.json()['wind']['speed']

        temp_unit = 'K'
        if units == "metric":
            temp_unit = 'C'
        elif units == "imperial":
            temp_unit = 'F'

        pad_to = 13
        print(f"{Fore.MAGENTA}{'location:':<{pad_to}s}{Fore.WHITE}{city}")
        print(f"{Fore.BLUE}{'country:':<{pad_to}s}{Fore.WHITE}{country}")
        print(f"{Fore.YELLOW}{'time:':<{pad_to}s}{Fore.WHITE}{weather_time} ({time})")
        print(f"{Fore.GREEN}{'temperature:':<{pad_to}s}{Fore.WHITE}{temp:.1f}°{temp_unit}")
        print(f"{Fore.CYAN}{'weather:':<{pad_to}s}{Fore.WHITE}{weather}")
        print(f"{Fore.RED}{'wind:':<{pad_to}s}{Fore.WHITE}{wind} m/s")

@click.group()
@click.option(
    '--api-key', '-a',
    type=str,
    envvar="OPENWEATHERMAP_KEY",
    help='open weather map api key'
)
@click.option(
    '--config', '-c',
    type=click.Path(),
    default='~/.owm_api_key.cfg',
)
@click.pass_context
def main(ctx, api_key, config):
    """
    A simple weather script using the open weather map api.

    API reference: http://openweathermap.org/api
    """
    config_file = os.path.expanduser(config)

    if not api_key and os.path.exists(config_file):
        print(f"reading config: {config_file}")
        with open(config_file) as cfg:
            config_json = json.load(cfg)
            api_key = config_json['api_key']

    ctx.obj = {
        'api_key': api_key,
        'config': config_file
    }

@main.command()
@click.pass_context
def save_config(ctx):
    """
    Save API key
    """
    config_file = ctx.obj['config']

    api_key = click.prompt(
        "save API key",
        default=ctx.obj.get('api_key', '')
    )

    config_json = {
        'api_key': api_key
    }

    with open(config_file, 'w') as cfg:
        json.dump(config_json, cfg)

@main.command()
@click.argument('location')
@click.option(
    '--units', '-u', default='metric',
    type=click.Choice(['standard', 'metric', 'imperial']),
    help='units of measurement'
)
@click.option(
    '--time', '-t', default='local',
    type=click.Choice(['local', 'utc']),
    help='print local or utc time'
)
@click.option(
    '--json', '-j', is_flag=True,
    help='print json response'
)
@click.option(
    '--query', '-q', is_flag=True,
    help='print api query'
)
@click.pass_context
def current(ctx, location, units, time, json, query):
    """
    get the current weather. location can be a town/city name and optionally an ISO 3166 country code.
    e.g 'Melbourne' or 'Melbourne, AU'
    """
    colorama.init(autoreset=True)

    print_current_weather(location, ctx.obj['api_key'], units, time, json, query)

if __name__ == "__main__":
    main()
