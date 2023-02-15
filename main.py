import binvox_rw

def main():
    with open('data/6873b186-51ab-401d-b5e3-7b0061e1e048.stl00-1.binvox', 'rb') as f:
        binvox_model = binvox_rw.read_as_3d_array(f)
    print(binvox_model.data)
    
if __name__ == "__main__":
    main()
    
    