import os,stat

def copyfileobj(fsrc, fdst, start, end, length=1024 * 1024):
    fsrc.seek(start)
    while start<=fsrc.tell()<end:
        
        if fsrc.tell()+length>end:
            length = end - fsrc.tell()
        buf = fsrc.read(length)
        
        if not buf:
            break
        fdst.write(buf)
    return fsrc.tell()

def split(file,num):
    size = os.lstat(file).st_size
    offset = size//num
    print(size,num,offset)
    ret = 0
    for i in range(num):
        with open(file, "rb") as fsrc:
            with open(f"{file}.part{i}", "wb") as fdst:
                if i == num-1:
                    ret = copyfileobj(fsrc, fdst, ret, size, min(1024*1024,size))
                else:
                    ret = copyfileobj(fsrc, fdst, ret, ret + offset, min(1024*1024,size))

def combine(files,name='',location='.'):
    if name=='':
        name = os.path.splitext(files[0])[0]
    with open(name,"wb") as core:
        for file in files:
            with open(file,'rb') as add:
                copyfileobj(add,core,0,os.lstat(file).st_size,1024*1024)

def main():
    choice = input("1. Combine\n2. Split\n>")
    if choice == '1':
        location = input("Where are the files: ").strip('"')
        file_name = input('file name after combining(with extension): ')
        bulk = [(x,z) for x,y,z in os.walk(location)]
        filtered = [os.path.join(x,y) for x,z in bulk if z for y in z if '.part' in os.path.splitext(y)[1]]
        combine(sorted(filtered),file_name,location)
    elif choice == '2':
        file = input("File to be split(location): ").strip('"')
        num = input("How many pieces: ")
        split(file,int(num))
    else:
        print("invalid input!")

main()