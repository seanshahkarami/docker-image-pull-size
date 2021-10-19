import argparse
import subprocess
import json
import pandas as pd


def infer_ref(s):
    parts = s.split("/")
    if ":" not in parts[-1]:
        parts[-1] = f"{parts[-1]}:latest"
    if len(parts) == 1:
        return "/".join(["docker.io", "library"] + parts)
    if len(parts) == 2:
        return "/".join(["docker.io"] + parts)
    if len(parts) == 3:
        return "/".join(parts)
    raise ValueError("invalid docker image ref")


def inspect_ref(ref):
    ref = infer_ref(ref)
    output = subprocess.check_output(["docker", "buildx", "imagetools", "inspect", "--raw", ref])
    results = json.loads(output)
    return results


def get_manifest_layers(ref, arch):
    ref = infer_ref(ref)
    results = inspect_ref(ref)
    for m in results["manifests"]:
        # TODO check os too
        if m["platform"]["architecture"] != arch:
            continue
        ref = f"{ref}@{m['digest']}"
        yield from inspect_ref(ref)["layers"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", default="amd64", help="arch to check")
    parser.add_argument("images", nargs="+", help="list of calendars")
    args = parser.parse_args()

    history = [
        {"name": "scratch", "size": 0, "layers": 0},
    ]

    cache = {}

    for image in args.images:
        for layer in get_manifest_layers(image, args.arch):
            digest = layer["digest"]
            if digest not in cache:
                cache[digest] = layer
        history.append({
            "name": image,
            "size": sum(l["size"]/1024**2 for l in cache.values()),
            "layers": len(cache),
        })

    df = pd.DataFrame(history)
    df["size_delta"] = df["size"].diff()
    df["layers_delta"] = df["layers"].diff()
    print(df.fillna(0))


if __name__ == "__main__":
    main()
