from db.dependencies import get_supabase

def main():
    sb = get_supabase()

    # try listing the tables
    try:
        resp = sb.table("requests").select("id").limit(1).execute()
        print("✅ Connected to Supabase")
        print("First request row (if any):", resp.data)
    except Exception as e:
        print("❌ Connection failed:", str(e))

if __name__ == "__main__":
    main()
