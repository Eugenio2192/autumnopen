from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from src.tools.config_loader import Configuration
from src.homogenization.data_operations import PowerPlantMatching
import math
import pandas as pd
import numpy as np
import random
from pathlib import Path
config = Configuration.get_instance()
io = config["IO"]
local_config = config["InputHomogenization"]

random_forest_config_all = local_config["RandomForest"]
regression_config = local_config["RegressionConfig"]

param_grid = {
    'bootstrap': [True],
    'max_depth': [1, 2, 3, 4, 5, 6, 7, 8],
    'max_samples': [0.5, 0.6, 0.7, 0.8, 0.9],
    'n_estimators': [20, 100, 200, 500]}


def ppm_regression_data(data):
    """
    Create subset of regression columns from input
    """
    x_cols = regression_config["X_columns"]
    y_col = regression_config["y_column"]
    columns = x_cols + [y_col]
    data = data.loc[:, columns]
    retrofitCol = regression_config['X_columns'][3]
    data.loc[:, retrofitCol] \
        = data.apply(lambda x: False if math.isnan(x[retrofitCol]) else True, axis=1)
    return data


def random_forest_regression(X, y, random_forest_config):
    """
    Perform Random Forest Regression
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=regression_config["split"]["test_size"],
        random_state=regression_config["split"]["random_state"])

    imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
    imputer = imputer.fit(X_train)
    X_train_imp = imputer.transform(X_train)

    model = RandomForestRegressor(**random_forest_config)
    model.fit(X_train_imp, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_pred, y_test, squared=False)
    return model, imputer, mse


def linear_regression(X, y):
    "Perform linerar Regression"
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=regression_config["split"]["test_size"],
        random_state=regression_config["split"]["random_state"])

    imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
    imputer = imputer.fit(X_train)
    X_train_imp = imputer.transform(X_train)

    model = LinearRegression()
    model.fit(X_train_imp, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_pred, y_test, squared=False)
    return model, imputer, mse


def rf_regression_efficiency_map(data):
    """
    Create regression dataset using RF
    """
    fuels = regression_config["Fuels"]
    data = data[data["Fueltype"].isin(fuels)]
    x_cols = regression_config["X_columns"]
    y_col = regression_config["y_column"]
    map = {}
    MSE = {}
    OOB = {}
    for fuel in fuels:
        model_data = data[data[y_col] != 0]
        model_data_fuel = model_data[model_data["Fueltype"] == fuel]
        regression_data = data[data["Fueltype"] == fuel]

        X = model_data_fuel.loc[:, x_cols].drop(columns=["Fueltype"])
        y = model_data_fuel.loc[:, y_col]
        random_forest_config = random_forest_config_all[fuel]
        model, imputer, mse = random_forest_regression(X, y, random_forest_config)

        X_prediction = regression_data[X.columns]
        X_pred_imp = imputer.transform(X_prediction)
        y_predicted = model.predict(X_pred_imp)
        MSE[fuel] = mse
        OOB[fuel] = model.oob_score_
        ids = regression_data.reset_index()["id"]

        map[fuel] = pd.concat([ids, pd.Series(y_predicted, name="predicted_efficiency")], axis=1).set_index(["id"])

        concat_map = pd.concat(map).reset_index().drop(columns=["level_0"])

    data = data.reset_index()
    data["predicted_efficiency"] = data.apply(
        lambda x: x.Efficiency if x.Efficiency != 0 else
        concat_map[concat_map.id == x.id]["predicted_efficiency"].values[0],
        axis=1)
    return data[["id", "predicted_efficiency"]], MSE, OOB


def linear_regression_efficiency_map(data):
    """
    Create regression dataset using Linear Regression
    """
    fuels = regression_config["Fuels"]
    print(fuels)
    data = data[data["Fueltype"].isin(fuels)]
    x_cols = ["Fueltype", "YearCommissioned"]
    y_col = regression_config["y_column"]
    map = {}
    MSE = {}
    for fuel in fuels:
        model_data = data[data[y_col] != 0]
        model_data_fuel = model_data[model_data["Fueltype"] == fuel]
        regression_data = data[data["Fueltype"] == fuel]

        X = model_data_fuel.loc[:, x_cols].drop(columns=["Fueltype"])
        y = model_data_fuel.loc[:, y_col]
        model, imputer, mse = linear_regression(X, y)

        X_prediction = regression_data[X.columns]
        X_pred_imp = imputer.transform(X_prediction)
        y_predicted = model.predict(X_pred_imp)
        MSE[fuel] = mse
        ids = regression_data.reset_index()["id"]

        map[fuel] = pd.concat([ids, pd.Series(y_predicted, name="predicted_efficiency")], axis=1).set_index(["id"])

        concat_map = pd.concat(map).reset_index().drop(columns=["level_0"])

    data = data.reset_index()
    data["predicted_efficiency"] = data.apply(
        lambda x: x.Efficiency if x.Efficiency != 0 else
        concat_map[concat_map.id == x.id]["predicted_efficiency"].values[0],
        axis=1)
    return data[["id", "predicted_efficiency"]], MSE


def naive_efficiency_map(data):
    """
    Create regression dataset using Naive Assumption
    """
    fuels = regression_config["Fuels"]
    data = data[data["Fueltype"].isin(fuels)]
    defaults = regression_config["NaiveValues"]
    data = data.reset_index()
    x_cols = ["Fueltype", "YearCommissioned"]
    data.loc[:, "predicted_efficiency"] = data.apply(
        lambda x: x.Efficiency if x.Efficiency != 0 else defaults[x.Fueltype],
        axis=1)
    MSE = {}
    for fuel in fuels:
        data = data[data["Efficiency"] != 0]
        model_data_fuel = data[data["Fueltype"] == fuel]
        X = model_data_fuel.loc[:, x_cols].drop(columns=["Fueltype"])
        y = model_data_fuel.loc[:, "Efficiency"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=regression_config["split"]["test_size"],
            random_state=regression_config["split"]["random_state"])
        y_pred = [defaults[fuel]] * len(y_test)
        mse = mean_squared_error(y_pred, y_test, squared=False)
        MSE[fuel] = mse
    return data[["id", "predicted_efficiency"]], MSE


def random_efficiency(data):
    """
    Assign random efficiency values
    """
    fuels = regression_config["Fuels"]
    data = data[data["Fueltype"].isin(fuels)]
    data = data.reset_index()
    defaults = regression_config["NaiveValues"]
    x_cols = ["Fueltype", "YearCommissioned"]
    data.loc[:, "predicted_efficiency"] = data.apply(
        lambda x: x.Efficiency if x.Efficiency != 0 else defaults[x.Fueltype],
        axis=1)
    MSE = {}
    for fuel in fuels:
        data = data[data["Efficiency"] != 0]
        model_data_fuel = data[data["Fueltype"] == fuel]
        X = model_data_fuel.loc[:, x_cols].drop(columns=["Fueltype"])
        y = model_data_fuel.loc[:, "Efficiency"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=regression_config["split"]["test_size"],
            random_state=regression_config["split"]["random_state"])

        y_pred = [random.uniform(np.min(y), np.max(y)) for i in range(len(y_test))]
        mse = mean_squared_error(y_pred, y_test, squared=False)
        MSE[fuel] = mse
    return data[["id", "predicted_efficiency"]], MSE


def ppm_proxy_efficiency(mode="random_forest", include_bio=False):
    """
    Add proxy efficiency values to power plant matching dataset
    """
    if include_bio:
        fuel_flag = "biofuels+conventional"
    else:
        fuel_flag = "conventional"
    if not Path(io["LOCAL_PPM_PATH"]).is_file():
        ppm = PowerPlantMatching(False)
    ppm = PowerPlantMatching.opsd_efficiency(fuel_flag)
    source_data = ppm.data
    model_data = ppm_regression_data(source_data)
    if mode == "naive":
        map, mse = naive_efficiency_map(model_data)
    elif mode == "linear":
        map, mse = linear_regression_efficiency_map(model_data)
    else:
        map, mse, oob = rf_regression_efficiency_map(model_data)

    fuels_f = regression_config["Fuels"].copy()

    output_data = source_data.merge(map, left_on="id", right_on="id", how="left")
    if include_bio:
        fuels_f.append("Bioenergy")
        output_data.loc[output_data["Fueltype"] == "Bioenergy",
                        ["predicted_efficiency"]] = local_config["RegressionConfig"]["NaiveValues"]["Bioenergy"]
    output_data = output_data[output_data["Fueltype"].isin(fuels_f)]
    return output_data


def gridsearch(data):
    fuels = regression_config["Fuels"]
    data = data[data["Fueltype"].isin(fuels)]
    x_cols = regression_config["X_columns"]
    y_col = regression_config["y_column"]
    GS = {}
    XS = {}
    YS = {}
    for fuel in fuels:
        model_data = data[data[y_col] != 0]
        model_data_fuel = model_data[model_data["Fueltype"] == fuel]
        regression_data = data[data["Fueltype"] == fuel]

        X = model_data_fuel.loc[:, x_cols].drop(columns=["Fueltype"])
        y = model_data_fuel.loc[:, y_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=regression_config["split"]["test_size"],
            random_state=regression_config["split"]["random_state"])

        imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
        imputer = imputer.fit(X_train)
        X_train_imp = imputer.transform(X_train)
        model = RandomForestRegressor()
        grid_search = GridSearchCV(estimator=model, param_grid=param_grid,
                                   cv=3, n_jobs=-1, verbose=2)
        grid_search.fit(X_train_imp, y_train)
        GS[fuel] = grid_search
        XS[fuel] = X_train_imp
        YS[fuel] = y_train
    return GS, XS, YS


def print_results_gs(GS, XS, YS):
    for fuel in GS.keys():
        print(fuel, ":")
        test_features = XS[fuel]
        test_labels = YS[fuel]
        gs = GS[fuel]
        print(gs.best_params_)
        best_grid = gs.best_estimator_
        grid_accuracy = evaluate(best_grid, test_features, test_labels)
        print(grid_accuracy)


def evaluate(model, test_features, test_labels):
    predictions = model.predict(test_features)
    errors = abs(predictions - test_labels)
    mape = 100 * np.mean(errors / test_labels)
    accuracy = 100 - mape
    print('Model Performance')
    print('Average Error: {:0.4f} degrees.'.format(np.mean(errors)))
    print('Accuracy = {:0.2f}%.'.format(accuracy))

    return accuracy


def evaluate_approaches():
    ppm = PowerPlantMatching.opsd_efficiency()
    source_data = ppm.data
    model_data = ppm_regression_data(source_data)
    _, mserf, _ = rf_regression_efficiency_map(model_data)
    _, mseli = linear_regression_efficiency_map(model_data)
    _, msena = naive_efficiency_map(model_data)
    _, msern = random_efficiency(model_data)
    return mserf, mseli, msena, msern


def create_evaluation_dictionary(tries):
    eval_map = {}
    for fuel in ["Hard Coal", "Lignite", "Natural Gas"]:
        eval_map[fuel] = {}
        eval_map[fuel]["rf"] = []
        eval_map[fuel]["li"] = []
        eval_map[fuel]["na"] = []
        eval_map[fuel]["rn"] = []
    for i in range(tries):
        regression_config["split"]["random_state"] = random.randint(0, 100)
        mserf, mseli, msena, msern = evaluate_approaches()
        for fuel in ["Hard Coal", "Lignite", "Natural Gas"]:
            eval_map[fuel]["rf"].append(mserf[fuel])
            eval_map[fuel]["li"].append(mseli[fuel])
            eval_map[fuel]["na"].append(msena[fuel])
            eval_map[fuel]["rn"].append(msern[fuel])
    return eval_map
