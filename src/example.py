import mod.download as dl

filing_df = dl.clerk_filings("Gaetz")
df_filtered = filing_df[filing_df["Filing"] == "FD Original"]
df_filtered = df_filtered.assign(images=filing_df["href"].apply(lambda x: dl.image_from_endpoint(x)))
first_pdf = df_filtered["images"].iloc[0][1]
first_page = first_pdf[0]
first_page.save("../output/example.png")