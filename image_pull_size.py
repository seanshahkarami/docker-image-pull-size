import argparse
import subprocess
import json
import pandas as pd


def expand_ref(s):
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
    return json.loads(
        subprocess.check_output(
            ["docker", "buildx", "imagetools", "inspect", "--raw", ref]
        )
    )


def get_layers(ref, arch):
    ref = expand_ref(ref)
    resp = inspect_ref(ref)
    media_type = resp["mediaType"]

    if media_type == "application/vnd.docker.distribution.manifest.list.v2+json":
        for m in resp["manifests"]:
            if m["platform"]["architecture"] != arch:
                continue
            digest_ref = f"{ref}@{m['digest']}"
            yield from get_layers(digest_ref, arch)
    elif media_type == "application/vnd.docker.distribution.manifest.v2+json":
        yield from inspect_ref(ref)["layers"]
    else:
        raise TypeError(f"unknown mediaType {media_type!r}")


def mbstr(x):
    return f"{x/1024**2:0.2f} MB"


def pct(x):
    return f"{x:0.2%}"


def default_arch():
    import platform
    machine = platform.machine()
    if machine == "x86_64":
        return "amd64"
    if machine == "aarch64":
        return "arm64"
    return "amd64"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--arch", choices=["amd64", "arm64"], help="arch to use"
    )
    parser.add_argument("images", nargs="+", help="list of calendars")
    args = parser.parse_args()

    if args.arch is None:
        args.arch = default_arch()
        print(f"detected arch {args.arch}")

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
    df["size_total_pct"] = df["size_total"] / df["size_total"].iloc[-1]

    df["size_delta"] = df["size_total"].diff()
    df["layers_delta"] = df["layers_total"].diff()
    df["size_delta_pct"] = df["size_total_pct"].diff()
    df = df.fillna(0)

    # format data
    df["size_total"] = df["size_total"].apply(mbstr)
    df["size_total_pct"] = df["size_total_pct"].apply(pct)
    df["size_delta"] = df["size_delta"].apply(mbstr)
    df["size_delta_pct"] = df["size_delta_pct"].apply(pct)
    df["layers_delta"] = df["layers_delta"].apply(int)

    # print results
    fields = [
        "name",
        "size_total",
        "size_total_pct",
        "size_delta",
        "size_delta_pct",
        "layers_total",
        "layers_delta",
    ]

    print(f"image layer summary (arch: {args.arch})")
    print(df[fields].to_string())


if __name__ == "__main__":
    main()
