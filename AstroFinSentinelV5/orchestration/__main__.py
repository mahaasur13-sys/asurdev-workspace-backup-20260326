# Main entry point with dual-mode + graceful degradation

def main():
    import sys
    import asyncio
    import traceback
    
    args = sys.argv[1:]
    
    # Parse flags
    masfactory = '--masfactory' in args or '--karl' in args
    masfactory = '--masfactory' in args or '--karl' in args
    
    # Remove flags from args
    clean_args = [a for a in args if not a.startswith('--')]
    query = ' '.join(clean_args) if clean_args else 'Analyze BTC'
    symbol = 'BTCUSDT'
    timeframe = 'SWING'
    
    if masfactory:
        print("\n[MASFactory] Mode: ENABLED")
        print("[MASFactory] Attempting topology build + execution...")
        try:
            from orchestration.sentinel_v5_mas import run_sentinel_v5_mas
            result = asyncio.run(run_sentinel_v5_mas(
                user_query=query,
                symbol=symbol,
                timeframe=timeframe,
            ))
            print(f"[MASFactory] Completed successfully")
            print(result)
            return
        except Exception as e:
            print(f"[MASFactory] ERROR: {e}")
            print("[MASFactory] Falling back to legacy mode...")
            traceback.print_exc()
    
    # Legacy mode (unchanged)
    print("[MASFactory] Mode: DISABLED (legacy)")
    from orchestration import karl_cli
    karl_cli.main()


if __name__ == "__main__":
    main()
