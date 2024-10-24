import pandas as pd
import argparse
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Select model combinations based on AC scores.")
    parser.add_argument('--data', type=str, choices=['A', 'C', 'AC', 'random', 'Ar'], required=True, help="Type of data to use for training.")
    parser.add_argument('--model', type=str, choices=['linear', 'polynomial'], required=True, help="Type of model to use for training.")
    parser.add_argument('--file_name', type=str, required=True, help="Name of the output CSV file.")

    args = parser.parse_args()

    df = pd.read_csv('/data/yangzhao/dy/Modality-Gap/policy/ablations_t.csv')

    # Define the parameters
    benchmarks = ["mmbench_en", "mme", "mmmu_val", "ok_vqa", "textvqa_val", "vizwiz_vqa_val", "scienceqa_img", "seed_image"]
    train_models = ["CLIP336", "CLIP224", "OpenCLIP", "DINOv2", "SDim", "SD1.5", "SDXL", "DiT", "SD3", "SD2.1", "SigLIP", "CLIP224+DINOv2", "CLIP336+DINOv2"]

    # Initialize a dictionary to store the results
    results = {}
    results['train_mse'] = []
    results['train_r2'] = []

    # Normalie the data
    def normalize(series):
        return (series - series.min()) / (series.max() - series.min())

    # calculate the normalized values
    df["mean_normed_a"] = df[[f'{benchmark}_average' for benchmark in benchmarks]].apply(normalize).mean(axis=1)
    df["mean_normed_y"] = df[benchmarks].apply(normalize).mean(axis=1)
    df["mean_normed_c"] = normalize(df['corres'])

    # Loop through the combinations and compute the average error rates


    train_df = df[df['model'].isin(train_models)]

    normalized_train_y = train_df["mean_normed_y"]

    if args.data == 'AC':
        normalized_train_X = train_df[['mean_normed_a', 'mean_normed_c']]
    elif args.data == 'random' and args.model == 'polynomial':
        normalized_train_X = train_df[['mean_normed_a', 'mean_normed_c']]
        column_names = normalized_train_X.columns
        num_rows = len(normalized_train_X)
        normalized_train_X = pd.DataFrame(np.random.rand(num_rows, len(column_names)), columns=column_names)
    elif args.data == 'random' and args.model == 'linear':
        normalized_train_X = train_df[['mean_normed_a']]
        column_names = normalized_train_X.columns
        num_rows = len(normalized_train_X)
        normalized_train_X = pd.DataFrame(np.random.rand(num_rows, len(column_names)), columns=column_names)
    elif args.data == 'A' and args.model == 'polynomial':
        normalized_train_X = train_df[['mean_normed_a', 'mean_normed_a']]
    elif args.data == 'A' and args.model == 'linear':
        normalized_train_X = train_df[['mean_normed_a']]
    elif args.data == 'C' and args.model == 'polynomial':
        normalized_train_X = train_df[['mean_normed_c', 'mean_normed_c']]
    elif args.data == 'C' and args.model == 'linear':
        normalized_train_X = train_df[['mean_normed_a']]
    elif args.data == 'Ar' and args.model == 'polynomial':
        normalized_train_X = train_df[['mean_normed_a']].copy()  # Start with 'normed_a'
        # Generate a random column with the same number of rows
        random_column = pd.DataFrame(np.random.rand(len(normalized_train_X), 1), columns=['random'])
        # Concatenate the 'normed_a' and random column
        normalized_train_X = pd.concat([normalized_train_X, random_column], axis=1)

    # Polynomial regression (degree 2)
    if args.model == 'polynomial':
        poly = PolynomialFeatures(degree=2)
        print(normalized_train_X.shape)
        normalized_train_X = poly.fit_transform(normalized_train_X)
        print(normalized_train_X.shape)
    model = LinearRegression()
    model.fit(normalized_train_X, normalized_train_y)
    train_pred = model.predict(normalized_train_X)
    train_mse = np.mean((normalized_train_y - train_pred) ** 2)
    train_r2 = r2_score(normalized_train_y, train_pred)

    results['train_mse'].append(train_mse)
    results['train_r2'].append(train_r2)
    # print(benchmark, train_r2)
    # results[f'{benchmark}_A'] = df["normed_a"].copy()
    # results[f'{benchmark}_C'] = df["normed_c"].copy()
        

    # Convert the results dictionary to a DataFrame
    results_df = pd.DataFrame(results)

    # Save the DataFrame to a CSV file
    results_df.to_csv(f'/data/yangzhao/dy/Modality-Gap/outputs/{args.file_name}', index=False)

if __name__ == "__main__":
    main()
