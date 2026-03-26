import torch
import gc

if __name__ == "__main__":
    if torch.cuda.is_available():
        print("Vyprazdňuji CUDA cache...")
        torch.cuda.empty_cache()
        gc.collect() # Pomůže uvolnit i Python garbage collector
        print("CUDA cache vyprázdněna.")
    else:
        print("CUDA není k dispozici, nelze vyprázdnit cache.")