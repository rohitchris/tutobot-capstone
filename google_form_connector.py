from sheets_helper import read_sheet, write_sheet
from drive_helper import create_folder, upload_file

from agents import run_generation_pipeline

def run_pipeline():
    print("🔄 Checking Google Form submissions...")

    df = read_sheet("form_responses")

    # Add Status column if missing
    if "Status" not in df.columns:
        df["Status"] = ""

    pending_rows = df[df["Status"] != "Completed"]

    if pending_rows.empty:
        print("✨ No new form responses. All caught up!")
        return

    for index, row in pending_rows.iterrows():
        teacher = row["Teacher Name"]
        print(f"⚡ Processing request by: {teacher}")

        # Step 1 — Create a Drive folder for this teacher
        folder_id = create_folder(teacher)

        # Step 2 — Use the main agent to generate content
        outputs = run_generation_pipeline(
            grade=row["Grade / Class"],
            subject=row["Subject"],
            topics=row["Topics to Cover"],
            weeks=row["Week Duration"],
            classes_per_week=row["Classes per Week"]
        )

        uploaded_links = []
        for file_path in outputs:
            link = upload_file(file_path, folder_id)
            uploaded_links.append(link)

        # Step 3 — Write back to Sheet
        write_sheet(
            "form_responses",
            index,
            {
                "Status": "Completed",
                "Drive Folder": f"https://drive.google.com/drive/folders/{folder_id}",
                "Generated Files": ", ".join(uploaded_links)
            }
        )

        print("🎉 Done!")

if __name__ == "__main__":
    run_pipeline()
