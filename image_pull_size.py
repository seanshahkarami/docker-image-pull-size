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
    body = subprocess.check_output(
        ["docker", "buildx", "imagetools", "inspect", "--raw", ref]
    )
    return json.loads(body)


def get_layers(ref, arch):
    ref = infer_ref(ref)
    resp = inspect_ref(ref)
    media_type = resp["mediaType"]

    if media_type == "application/vnd.docker.distribution.manifest.list.v2+json":
        for m in resp["manifests"]:
            if m["platform"]["architecture"] != arch:
                continue
            ref = f"{ref}@{m['digest']}"
            yield from get_layers(ref, arch)
    elif media_type == "application/vnd.docker.distribution.manifest.v2+json":
        yield from inspect_ref(ref)["layers"]
    else:
        raise TypeError(f"unknown mediaType {media_type!r}")


def mbstr(r):
    return f"{r/1024**2:0.2f} MB"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", default="amd64", help="arch to check")
    parser.add_argument("images", nargs="+", help="list of calendars")
    args = parser.parse_args()

    history = [
        {"name": "scratch", "size_total": 0, "layers_total": 0},
    ]

    cache = {}

    for image in args.images:
        # add all image layers to the cache, as needed
        for layer in get_layers(image, args.arch):
            digest = layer["digest"]
            if digest not in cache:
                cache[digest] = layer
        # update history
        history.append(
            {
                "name": image,
                "size_total": sum(l["size"] for l in cache.values()),
                "layers_total": len(cache),
            }
        )

    df = pd.DataFrame(history)
    df["size_delta"] = df["size_total"].diff()
    df["layers_delta"] = df["layers_total"].diff()
    df = df.fillna(0)

    # format data
    df["size_total"] = df["size_total"].apply(mbstr)
    df["size_delta"] = df["size_delta"].apply(mbstr)
    df["layers_delta"] = df["layers_delta"].apply(int)

    # print results
    print(df[["name", "size_total", "size_delta", "layers_total", "layers_delta"]])


if __name__ == "__main__":
    main()
