import random, threading, time, zmq, socket, argparse
import matplotlib.pyplot as plt
B = 32  # number of bits of precision in each random integer

def ones_and_zeros(digits):
    """Express `n` in at least `d` binary digits, with no special prefix."""
    return bin(random.getrandbits(digits)).lstrip('0b').zfill(digits)

def client(zcontext, in_url, out_url):
    #Client node for N input and plotting x,y values
    try: #exception handling incase of invalid values entered
        N = int(input("Enter numbers of data points : "))
    except ValueError:
        print('Invalid value')
        quit()

    osock = zcontext.socket(zmq.PUSH) #client sends input N to bitsource
    osock.connect(out_url)
    osock.send_string(str(N))
    
    isock = zcontext.socket(zmq.PULL) #client recieves tally information from tally   
    isock.bind(in_url)
    
    for i in range(int(N)):
        x = isock.recv_string()
        y = float(isock.recv_string())
        print('Iteration : {0} Pi value : {1}'.format(x, y))
        plt.plot(x, y, 'o') #plots iteration number and pi-value 
        plt.pause(0.1)
        plt.xlabel("Pi value (total {0} iterations)".format(N))
        ax = plt.gca()
        ax.axes.xaxis.set_ticks([])
    plt.show()


def bitsource(zcontext, in_url, out_url):
    """Produce random points in the unit square."""
    
    isock = zcontext.socket(zmq.PULL) #bitsource receives N from client
    isock.bind(in_url)
    N = isock.recv_string() #N value received from client
     
    osock = zcontext.socket(zmq.PUB) #bitsource sends random bits
    osock.bind(out_url)
    print("Input Url : ", in_url)
    print("Output Url : ", out_url)
    for i in range(int(N)):
        time.sleep(0.1)
        a = ones_and_zeros(B*2)
        osock.send_string(a)
        print("Publishing : ", a);

def always_yes(zcontext, in_url, out_url):
    """Coordinates in the lower-left quadrant are inside the unit circle."""
    
    isock = zcontext.socket(zmq.SUB) #receives random bits from bitsource if b'00'
    isock.connect(in_url)
    isock.setsockopt(zmq.SUBSCRIBE, b'00')
    
    osock = zcontext.socket(zmq.PUSH)
    osock.connect(out_url)
    print("Input Url : ", in_url)
    print("Output Url : ", out_url)
    while True:
        time.sleep(0.1)
        print("Receiving : ", isock.recv_string())
        osock.send_string('Y')

def judge(zcontext, in_url, pythagoras_url, out_url):
    """Determine whether each input coordinate is inside the unit circle."""
    isock = zcontext.socket(zmq.SUB) #receives random bits from bitsource if b'01', b'10', b'11'
    isock.connect(in_url)
    
    for prefix in b'01', b'10', b'11':
        isock.setsockopt(zmq.SUBSCRIBE, prefix)
    psock = zcontext.socket(zmq.REQ)
    psock.connect(pythagoras_url)
    
    osock = zcontext.socket(zmq.PUSH)
    osock.connect(out_url)
    print("Input Url : ", in_url)
    print("Output Url : ", out_url)
    print("Pythagoras Url : ", pythagoras_url)
    unit = 2 ** (B * 2)
    while True:
        time.sleep(0.1)
        bits = isock.recv_string()
        print("Receiving : ", bits)
        n, m = int(bits[::2], 2), int(bits[1::2], 2)
        psock.send_json((n, m))
        sumsquares = psock.recv_json()
        osock.send_string('Y' if sumsquares < unit else 'N')

def pythagoras(zcontext, url):
    """Return the sum-of-squares of number sequences."""
    
    zsock = zcontext.socket(zmq.REP)
    zsock.bind(url)
    print("url : ", url)
    while True:
        numbers = zsock.recv_json()
        print("Receiving : ", numbers)
        zsock.send_json(sum(n * n for n in numbers))
        print("Sending : ", sum(n * n for n in numbers))

def tally(zcontext, in_url, out_url):
    """Tally how many points fall within the unit circle, and print pi."""
    isock = zcontext.socket(zmq.PULL) #receives decisions from judge and always_yes
    isock.bind(in_url)
    
    osock = zcontext.socket(zmq.PUSH) #sends tally information to client
    osock.connect(out_url)
    print("Input Url : ", in_url)
    print("Output Url : ", out_url)
    p = q = 0
    while True:
        decision = isock.recv_string()
        print("Receiving : ", decision)
        q += 1
        if decision == 'Y':
            p += 4
        x = str(q) #sends x and y values to client
        y = str(p/q)
        print("Sending : ", y) 
        osock.send_string(x)
        osock.send_string(y)
    
    

def main(zcontext):
    #addresses used for simulating on multiple terminals
    addr1 = 'tcp://127.0.0.1:6700'
    addr2 = 'tcp://127.0.0.2:6701'
    addr3 = 'tcp://127.0.0.3:6702'
    addr4 = 'tcp://127.0.0.4:6703'
    addr5 = 'tcp://127.0.0.5:6704'
    
    choices = {'client': client, 'bitsource': bitsource, 'always_yes': always_yes, 'judge': judge, 'pythagoras':pythagoras, 'tally': tally}
    parser = argparse.ArgumentParser() #Argument Parser
    parser.add_argument('role', choices = choices)
    args = parser.parse_args()
    function = choices[args.role]
 
    if args.role=='client': #performs different functions depending on passed argument
        function(zcontext, addr1, addr2)
    elif args.role=='bitsource':
        function(zcontext, addr2, addr3)
    elif args.role=='always_yes':
        function(zcontext, addr3, addr5)
    elif args.role=='judge':
        function(zcontext, addr3, addr4, addr5)
    elif args.role=='pythagoras':
        function(zcontext, addr4)
    elif args.role=='tally':
        function(zcontext, addr5, addr1)
    
    

if __name__ == '__main__':
    main(zmq.Context())