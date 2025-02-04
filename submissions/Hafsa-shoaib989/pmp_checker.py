import sys

# Count the number of trailing 1s in the binary representation of n.
def count_trailing_ones(n):
    if n == 0:
        return 0
    count = 0
    while (n & 1) == 1:
        count += 1
        n >>= 1
    return count

def main():
    if len(sys.argv) != 5:
        print("Usage: program <pmp_config> <address> <mode> <operation>")
        sys.exit(1)

    config_file = sys.argv[1]
    address_str = sys.argv[2]
    mode = sys.argv[3]
    operation = sys.argv[4]

    address = int(address_str, 16)   # Parse the physical address (hex with 0x prefix)

    try:
        with open(config_file, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: File {config_file} not found.")
        sys.exit(1)

    if len(lines) != 128:
        print("Invalid PMP configuration file: expected 128 lines.")
        sys.exit(1)

    # Parse PMPcfg and PMPaddr entries
    cfgs = []
    addrs = []
    for i in range(64):
        cfg_line = lines[i]
        cfgs.append(int(cfg_line, 16))

    for i in range(64, 128):
        addr_line = lines[i]
        addrs.append(int(addr_line, 16))

    # Check each PMP entry in order (0 to 63)
    matching_entry = None
    for i in range(64):
        cfg = cfgs[i]
        # Extract fields from cfg byte
        L = (cfg >> 7) & 0x1
        A = (cfg >> 3) & 0x3
        X = (cfg >> 2) & 0x1
        W = (cfg >> 1) & 0x1
        R = cfg & 0x1

        if A == 0:
            continue  # Entry is disabled

        pmpaddr = addrs[i]
        pmpaddr_val = pmpaddr << 2  # Shift left by 2 to get actual address part

        # Determine address range based on A field
        if A == 1:  # TOR (Top of Range)
            if i == 0:
                lower = 0
                upper = pmpaddr_val
            else:
                prev_pmpaddr = addrs[i-1] << 2
                lower = prev_pmpaddr
                upper = pmpaddr_val

            if lower >= upper:
                continue  # Invalid range, no match

            if address >= lower and address < upper:
                matching_entry = (L, R, W, X)
                break

        elif A == 2:  # NA4 (Naturally Aligned 4-byte)
            start = pmpaddr_val
            end = start + 4
            if address >= start and address < end:
                matching_entry = (L, R, W, X)
                break

        elif A == 3:  # NAPOT (Naturally Aligned Power-of-Two)
            trailing_ones = count_trailing_ones(pmpaddr)
            size = 2 ** (trailing_ones + 3)
            base = (pmpaddr_val) & ~(size - 1)
            end = base + size
            if address >= base and address < end:
                matching_entry = (L, R, W, X)
                break

    # Determine access fault
    if matching_entry is not None:
        L, R, W, X = matching_entry
        # Check permissions
        if mode == 'M' and L == 0:
            allowed = True
        else:
            if operation == 'R':
                allowed = (R == 1)
            elif operation == 'W':
                allowed = (W == 1)
            elif operation == 'X':
                allowed = (X == 1)
            else:
                allowed = False  # Invalid operation (unreachable per problem statement)

        print("Access Fault" if not allowed else "No Access Fault")
    else:
        # No matching entry
        if mode == 'M':
            print("No Access Fault")
        else:
            # S or U mode, and PMP entries are implemented (all 64 in config)
            print("Access Fault")

if __name__ == "__main__":
    main()
