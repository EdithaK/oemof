# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm


# global plotting options
plt.rcParams.update(plt.rcParamsDefault)
matplotlib.style.use('ggplot')
plt.rcParams['lines.linewidth'] = 2.5
plt.rcParams['axes.facecolor'] = 'silver'
plt.rcParams['xtick.color'] = 'k'
plt.rcParams['ytick.color'] = 'k'
plt.rcParams['text.color'] = 'k'
plt.rcParams['axes.labelcolor'] = 'k'
plt.rcParams.update({'font.size': 10})
plt.rcParams['image.cmap'] = 'Blues'

# read file
file = ('results/'
        'scenario_nep_2035_ee_plus_25_2016-08-09 16:27:06.904477_DE.csv')

df_raw = pd.read_csv(file, parse_dates=[0], index_col=0, keep_date_col=True)
df_raw.head()
df_raw.columns


# %% plot fundamental and regression prices (1 year)

df = df_raw[['duals']]

price_real = pd.read_csv('price_eex_day_ahead_2014.csv')
price_real.index = df_raw.index

df = pd.concat([price_real, df], axis=1)
df.columns = ['price_real', 'price_model']

df.plot(drawstyle='steps')
plt.xlabel('Zeit in h')
plt.ylabel('Preis in EUR/MWh')
plt.show()


# %% plot fundamental and regression prices (8 weeks)

df = df_raw[['duals']]

price_real = pd.read_csv('price_eex_day_ahead_2014.csv')
price_real.index = df_raw.index

df = pd.concat([price_real, df], axis=1)
df.columns = ['price_real', 'price_model']

df[(24 * 7)*8:(24 * 7)*16].plot(drawstyle='steps')
plt.xlabel('Zeit in h')
plt.ylabel('Preis in EUR/MWh')
plt.show()


# %% polynom fitting: residual load

# prepare dataframe for fit
residual_load = df_raw['DE_load'] + df_raw['AT_load'] + df_raw['LU_load'] - \
                df_raw['DE_wind'] - df_raw['AT_wind'] - df_raw['LU_wind'] - \
                df_raw['DE_solar'] - df_raw['AT_solar'] - df_raw['LU_solar']

# real prices
price_real = pd.read_csv('price_eex_day_ahead_2014.csv')
price_real.index = df_raw.index

df = pd.concat([residual_load, price_real, df_raw['duals']], axis=1)
df.columns = ['res_load', 'price_real', 'price_model']

# fit polynom of 3rd degree to price_real(res_load)
z = np.polyfit(df['res_load'], df['price_real'], 3)
p = np.poly1d(z)
df['price_polynom_res_load'] = p(df['res_load'])

df.plot.scatter(x='res_load', y='price_real')
plt.plot(df['res_load'],
         (
          z[0] * df['res_load'] ** 3 +
          z[1] * df['res_load'] ** 2 +
          z[2] * df['res_load'] ** 1 +
          z[3]
          ), color='red')
plt.xlabel('Residuallast in MW')
plt.ylabel('Day-Ahead Preis in EUR/MWh')

plt.show()


# %% dispatch plot (balance doesn't fit since DE/LU/AT are one bidding area)

file_name = 'scenario_nep_2014_2016-08-04 12:04:42.180425_DE.csv'

df = pd.read_csv('results/' + file_name, parse_dates=[0],
                 index_col=0, keep_date_col=True)

df_dispatch = pd.DataFrame()

# country code
cc = ['DE', 'LU', 'AT']

# get fossil and renewable power plants
fuels = ['run_of_river', 'biomass', 'solar', 'wind', 'uranium', 'lignite',
         'hard_coal', 'gas', 'mixed_fuels', 'oil', 'load', 'excess',
         'shortage']
for f in fuels:
    cols = [c for c in df.columns
            if f in c and any(substring in c
                              for substring in cc)]
    df_dispatch[f] = df[cols].sum(axis=1)

# get imports and exports and aggregate columns
cols = [c for c in df.columns
        if 'powerline' in c and any(substring in c
                                    for substring in cc)]
powerlines = df[cols]
exports = powerlines[[c for c in powerlines.columns
                      if c.startswith('DE_')]]
imports = powerlines[[c for c in powerlines.columns
                      if ('_' + 'DE' + '_' in c)]]
df_dispatch['imports'] = imports.sum(axis=1)
df_dispatch['exports'] = exports.sum(axis=1)

# get phs in- and outputs
phs_in = df[[c for c in df.columns if 'phs_in' in c and
            any(substring in c for substring in cc)]]
phs_out = df[[c for c in df.columns if 'phs_out' in c and
             any(substring in c for substring in cc)]]
phs_level = df[[c for c in df.columns if 'phs_level' in c and
                any(substring in c for substring in cc)]]
df_dispatch['phs_in'] = phs_in.sum(axis=1)
df_dispatch['phs_out'] = phs_out.sum(axis=1)
df_dispatch['phs_level'] = phs_level.sum(axis=1)

# MW to GW
df_dispatch = df_dispatch.divide(1000)

# dict with new column names
en_de = {'run_of_river': 'Laufwasser',
         'biomass': 'Biomasse',
         'solar': 'Solar',
         'wind': 'Wind',
         'uranium': 'Kernenergie',
         'lignite': 'Braunkohle',
         'hard_coal': 'Steinkohle',
         'gas': 'Gas',
         'mixed_fuels': 'Sonstiges',
         'oil': 'Öl',
         'phs_in': 'Pumpspeicher (Laden)',
         'phs_out': 'Pumpspeicher (Entladen)',
         'imports': 'Import',
         'exports': 'Export',
         'load': 'Last'}
df_dispatch = df_dispatch.rename(columns=en_de)

# area plot. gute woche: '2014-01-21':'2014-01-27'
cols = ['Biomasse', 'Laufwasser', 'Kernenergie', 'Braunkohle',
        'Steinkohle', 'Gas', 'Öl', 'Sonstiges', 'Solar', 'Wind',
        'Pumpspeicher (Entladen)', 'Import']
df_dispatch['2014-01-21':'2014-01-27'][cols] \
             .plot(kind='area', stacked=True, linewidth=0, legend='reverse',
                   cmap=cm.get_cmap('Spectral'))
plt.xlabel('Datum')
plt.ylabel('Leistung in  GW')
plt.ylim(0, max(df_dispatch.sum(axis=1)) * 0.4)
plt.show()

# %% duration curves for power plants
curves = pd.concat(
    [df_dispatch[col].sort_values(ascending=False).reset_index(drop=True)
     for col in df_dispatch], axis=1)
curves[['Kernenergie', 'Braunkohle', 'Steinkohle', 'Gas', 'Öl',
        'Sonstiges', 'Solar', 'Wind', 'Pumpspeicher (Entladen)',
        'Import', 'Export']].plot(cmap=cm.get_cmap('Spectral'))
plt.xlabel('Stunden des Jahres')
plt.ylabel('Leistung in GW')
plt.show()


# %% duration curves for all powerlines
pls = pd.concat(
    [powerlines[col].sort_values(ascending=False).reset_index(drop=True)
     for col in powerlines], axis=1)
pls.plot(legend='reverse', cmap=cm.get_cmap('Spectral'))
plt.xlabel('Stunden des Jahres')
plt.ylabel('Leistung in GW')
plt.show()


# %% duraction curve for one cable e.g. NordLink cable
cable = df_raw[['DE_NO_powerline', 'NO_DE_powerline']]
cable = pd.concat(
    [cable[col].sort_values(ascending=False).reset_index(drop=True)
     for col in cable], axis=1)
cable = cable.rename(columns={'DE_NO_powerline': 'DE-NO',
                              'NO_DE_powerline': 'NO-DE'})
cable.plot(legend='reverse', cmap=cm.get_cmap('Spectral'))
plt.xlabel('Stunden des Jahres')
plt.ylabel('Leistung in GW')
plt.ylim(0, max(cable.sum(axis=1)) * 1.2)
plt.show()


# %% duraction curve for prices
power_price_real = pd.read_csv('price_eex_day_ahead_2014.csv')
power_price_real.set_index(df_raw.index, drop=True, inplace=True)
power_price = pd.concat([power_price_real,
                         df_raw[['duals']]], axis=1)
power_price = pd.concat(
    [power_price[col].sort_values(ascending=False).reset_index(drop=True)
     for col in power_price], axis=1)
power_price.plot(legend='reverse', cmap=cm.get_cmap('Spectral'))
plt.xlabel('Stunden des Jahres')
plt.ylabel('Preis in EUR/MWh')
plt.show()


# %% scaling

df = df_raw[['duals']]
df['duals_x_1_5'] = df['duals'] + \
    (df['duals'].subtract(df['duals'].mean())) * 1.5
df['duals_x_2'] = df['duals'] + \
    (df['duals'].subtract(df['duals'].mean())) * 2
df['duals_x_2'] = df['duals'] + \
    (df['duals'].subtract(df['duals'].mean())) * 3

df[0:24*31].plot(drawstyle='steps')
plt.show()


# %% boxplot for prices: monthly

df = df_raw[['duals']]
df['dates'] = df.index
df['month'] = df.index.month

df_box = df.pivot(index='dates', columns='month', values='duals')

bp = df_box.boxplot(showfliers=False, showmeans=True, return_type='dict')
plt.xlabel('Monat', fontsize=20)
plt.ylabel('Preis in EUR/MWh', fontsize=22)
plt.tick_params(axis='y', labelsize=14)
plt.tick_params(axis='x', labelsize=14)
plt.legend('')

[[item.set_linewidth(2) for item in bp['boxes']]]
[[item.set_linewidth(2) for item in bp['fliers']]]
[[item.set_linewidth(2) for item in bp['medians']]]
[[item.set_linewidth(2) for item in bp['means']]]
[[item.set_linewidth(2) for item in bp['whiskers']]]
[[item.set_linewidth(2) for item in bp['caps']]]

[[item.set_color('k') for item in bp['boxes']]]
[[item.set_color('k') for item in bp['fliers']]]
[[item.set_color('k') for item in bp['medians']]]
[[item.set_color('k') for item in bp['whiskers']]]
[[item.set_color('k') for item in bp['caps']]]

[[item.set_markerfacecolor('k') for item in bp['means']]]

plt.show()

## %% spline interpolation
#
#df = df_raw[['duals']]
#
#price_real = pd.read_csv('price_eex_day_ahead_2014.csv')
#price_real.index = df_raw.index
#
#df = pd.concat([price_real, df], axis=1)
#df.columns = ['price_real', 'price_model']
#
## detect tableus with a constand price
#tableaus = np.where(df['price_model'] == df['price_model'].shift(1))
#tableaus = tableaus[0].tolist()
#
## set the tableaus to NaN
#df.reset_index(drop=True, inplace=True)
#df['no_tableaus'] = df[~df.index.isin(tableaus)]['price_model']
#df.index = df_raw.index
#
## check different interpolation methods
#df['linear'] = df['no_tableaus'].interpolate(method='linear')
#df['cubic'] = df['no_tableaus'].interpolate(method='cubic')
#
## plot
#df[0:24 * 7 * 8].plot(drawstyle='steps', subplots=False, sharey=True,
#                      linewidth=2)
#plt.show()
#
## statistical parameters
#df.corr()
#df.describe()


# %% comparison of prices for sensitivities

files = {
    'nep_2014_base':
        'scenario_nep_2014_2016-08-04 12:04:42.180425_DE.csv',
    'nep_2025_base':
        'scenario_nep_2025_2016-08-10 14:26:12.390085_DE.csv',
    'nep_2035_base':
        'scenario_nep_2035_2016-08-05 15:18:42.431986_DE.csv',
    'nep_2035_ee_plus_25':
        'scenario_nep_2035_ee_plus_25_2016-08-09 16:27:06.904477_DE.csv',
    'nep_2035_ee_minus_25':
        'scenario_nep_2035_ee_minus_25_2016-08-09 16:45:40.295183_DE.csv',
    'nep_2035_demand_plus_25':
        'scenario_nep_2035_demand_plus_25_2016-08-10 09:38:10.628613_DE.csv',
    'nep_2035_demand_minus_25':
        'scenario_nep_2035_demand_minus_25_2016-08-10 09:50:48.953929_DE.csv',
    'nep_2035_fuel_plus_25':
        'scenario_nep_2035_fuel_plus_25_2016-08-10 12:10:08.246319_DE.csv',
    'nep_2035_fuel_minus_25':
        'scenario_nep_2035_fuel_minus_25_2016-08-10 12:20:30.690439_DE.csv',
    'nep_2035_co2_plus_25':
        'scenario_nep_2035_co2_plus_25_2016-08-10 12:37:36.981611_DE.csv',
    'nep_2035_co2_minus_25':
        'scenario_nep_2035_co2_minus_25_2016-08-10 12:49:50.740375_DE.csv',
    'nep_2035_nordlink_plus_25':
        'scenario_nep_2035_nordlink_plus_25_2016-08-10 13:00:08.919877_DE.csv',
    'nep_2035_nordlink_minus_25':
        'scenario_nep_2035_nordlink_minus_25_2016-08-10 13:10:34.528303_DE.csv'
}

df_prices = pd.DataFrame(index=df_raw.index)

for k, v in files.items():
    df = pd.read_csv('results/' + v, parse_dates=[0],
                     index_col=0, keep_date_col=True)
    df.index = df_prices.index
    df_prices[k] = df['duals']

# sort by column names
df_prices.sort_index(inplace=True, axis=1)

# save as csv
df_prices.to_csv('prices_all_scenarios_with_sensivities.csv')

# boxplot
df_prices.plot(kind='box', rot=90,
               color={'medians': 'k', 'boxes': 'k', 'whiskers': 'k',
                      'caps': 'k'})
plt.ylabel('Preis in EUR/MWh')
plt.tight_layout()
plt.show()

# histogram
df_prices[['nep_2014_base', 'nep_2035_demand_minus_25',
           'nep_2025_base', 'nep_2035_demand_plus_25',
           'nep_2035_base', 'nep_2035_co2_minus_25',
           'nep_2035_ee_minus_25', 'nep_2035_co2_plus_25',
           'nep_2035_ee_plus_25', 'nep_2035_nordlink_minus_25',
           'nep_2035_fuel_minus_25', 'nep_2035_nordlink_plus_25',
           'nep_2035_fuel_plus_25']] \
    .plot(kind='hist', bins=25, normed=True, subplots=True, sharex=True,
          sharey=True, layout=(7, 2), cmap=cm.get_cmap('Spectral'))
[ax.legend(loc='upper right') for ax in plt.gcf().axes]
plt.suptitle('Preis in EUR/MWh (25 Bins)', size=20)
plt.show()

# duration curves for all scenarios
df_prices_duration = pd.concat(
    [df_prices[col].sort_values(ascending=False).reset_index(drop=True)
     for col in df_prices], axis=1)
df_prices_duration.plot(legend='reverse', cmap=cm.get_cmap('Spectral'))
plt.xlabel('Stunden des Jahres')
plt.ylabel('Preis in EUR/MWh')
plt.tight_layout()
plt.show()

# duration curves for base scenarios
df_prices_duration[['nep_2014_base', 'nep_2025_base',
                    'nep_2035_base']].plot(legend='reverse',
                                           cmap=cm.get_cmap('Spectral'))
plt.xlabel('Stunden des Jahres')
plt.ylabel('Preis in EUR/MWh')
plt.tight_layout()
plt.show()


#df_prices['2035-01':'2035-02'].plot(drawstyle='steps')
#plt.show()


# %% plot of annual production for scenarios

files = {
    'nep_2014_base':
        'scenario_nep_2014_2016-08-04 12:04:42.180425_DE.csv',
    'nep_2025_base':
        'scenario_nep_2025_2016-08-10 14:26:12.390085_DE.csv',
    'nep_2035_base':
        'scenario_nep_2035_2016-08-05 15:18:42.431986_DE.csv',
    'nep_2035_ee_plus_25':
        'scenario_nep_2035_ee_plus_25_2016-08-09 16:27:06.904477_DE.csv',
    'nep_2035_ee_minus_25':
        'scenario_nep_2035_ee_minus_25_2016-08-09 16:45:40.295183_DE.csv',
    'nep_2035_demand_plus_25':
        'scenario_nep_2035_demand_plus_25_2016-08-10 09:38:10.628613_DE.csv',
    'nep_2035_demand_minus_25':
        'scenario_nep_2035_demand_minus_25_2016-08-10 09:50:48.953929_DE.csv',
    'nep_2035_fuel_plus_25':
        'scenario_nep_2035_fuel_plus_25_2016-08-10 12:10:08.246319_DE.csv',
    'nep_2035_fuel_minus_25':
        'scenario_nep_2035_fuel_minus_25_2016-08-10 12:20:30.690439_DE.csv',
    'nep_2035_co2_plus_25':
        'scenario_nep_2035_co2_plus_25_2016-08-10 12:37:36.981611_DE.csv',
    'nep_2035_co2_minus_25':
        'scenario_nep_2035_co2_minus_25_2016-08-10 12:49:50.740375_DE.csv',
    'nep_2035_nordlink_plus_25':
        'scenario_nep_2035_nordlink_plus_25_2016-08-10 13:00:08.919877_DE.csv',
    'nep_2035_nordlink_minus_25':
        'scenario_nep_2035_nordlink_minus_25_2016-08-10 13:10:34.528303_DE.csv'
}

df_dispatch = pd.DataFrame()

for k, v in files.items():
    df = pd.read_csv('results/' + v, parse_dates=[0],
                     index_col=0, keep_date_col=True)

    df_tmp = pd.DataFrame()

    # country code
    cc = ['DE', 'LU', 'AT']

    # get fossil and renewable power plants
    fuels = ['run_of_river', 'biomass', 'solar', 'wind', 'uranium', 'lignite',
             'hard_coal', 'gas', 'mixed_fuels', 'oil', 'load', 'excess',
             'shortage']
    for f in fuels:
        cols = [c for c in df.columns
                if f in c and any(substring in c
                                  for substring in cc)]
        df_tmp[f] = df[cols].sum(axis=1)

    # get imports and exports and aggregate columns
    cols = [c for c in df.columns
            if 'powerline' in c and any(substring in c
                                        for substring in cc)]
    powerlines = df[cols]
    exports = powerlines[[c for c in powerlines.columns
                          if c.startswith('DE_')]]
    imports = powerlines[[c for c in powerlines.columns
                          if ('_' + 'DE' + '_' in c)]]
    df_tmp['imports'] = imports.sum(axis=1)
    df_tmp['exports'] = exports.sum(axis=1)

    # get phs in- and outputs
    phs_in = df[[c for c in df.columns if 'phs_in' in c and
                any(substring in c for substring in cc)]]
    phs_out = df[[c for c in df.columns if 'phs_out' in c and
                 any(substring in c for substring in cc)]]
    phs_level = df[[c for c in df.columns if 'phs_level' in c and
                    any(substring in c for substring in cc)]]
    df_tmp['phs_in'] = phs_in.sum(axis=1)
    df_tmp['phs_out'] = phs_out.sum(axis=1)
    df_tmp['phs_level'] = phs_level.sum(axis=1)

    # MW to TW
    df_tmp = df_tmp.divide(1000000)

    # Sum up data (TWh) and adjust index
    df_tmp = df_tmp.sum().to_frame().transpose()
    df_tmp.reset_index(drop=True, inplace=True)
    df_tmp.index = [k]

    # append row
    df_dispatch = df_dispatch.append(df_tmp)

# sort by row index
df_dispatch.sort_index(inplace=True)

df_dispatch.sum(axis=1)

# plot
df_dispatch['load'] = df_dispatch['load'].multiply(-1)
df_dispatch['phs_in'] = df_dispatch['phs_in'].multiply(-1)
df_dispatch['exports'] = df_dispatch['exports'].multiply(-1)
df_dispatch['excess'] = df_dispatch['excess'].multiply(-1)

# check if balance fits
df_dispatch.drop(['phs_level'], axis=1).sum(axis=1)

cols = ['run_of_river', 'biomass', 'solar', 'wind', 'uranium', 'lignite',
        'hard_coal', 'gas', 'mixed_fuels', 'oil',  'phs_out',
        'imports', 'shortage',
        'load', 'phs_in', 'exports', 'excess']
df_dispatch[cols].plot(kind='bar', stacked=True, cmap=cm.get_cmap('Spectral'))
plt.title('Jährliche Stromproduktion nach Energieträgern')
plt.ylabel('TWh')
#plt.legend(loc='center left', ncol=11)
plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
#plt.tight_layout()
plt.show()

# %% dispatch of norwegian hydro power plants
