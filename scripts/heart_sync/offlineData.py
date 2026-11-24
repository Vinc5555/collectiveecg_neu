
class offlineDataManagement: 
    """
    Class to communicate with the "PSFTP" (polar simple file transfer protocol) and 
    retrieve offline measured data
    * first establish connection to PFTP 
    * create a request as a protobuf file (TODO : what should be the content ?)
    * Use PbPFtpOperation command ”GET” and set path to ”/U/0/” of the PtfpRe-
    quest class. Build the request class into PftpRequest protobuf file and then serialize
    the file into a byte array type. Create a request to the BlePsFtpClient client and
    give the serialized PftpRequest protobuf file as a parameter to the request. PTFP
    service will return a ByteBuffer response. Parse that response with PftpPDirectory
    class instance and you will get a list of directory entry. Find the desired files from
    the directory and retrieve the files on-by-one as described in the next chapter.

    """
    PFTP_UUID = "0000FEEE-0000-1000-8000-00805f9b34fb"
    PSFTP_UUID = "FB005C51-02E7-F387-1CAD-8ACD2D8DF0C8" # check difference with PFTP ?
    # "0000FEEE-0000-1000-8000-00805f9b34fb"

    def __init__(self, client):
        self.client = client # bleak client 

    def connect_to_pftp(self):
        """ connect to PFTP uuid """

    def create_protobuf_request(self):
        """ create request as protobuf file
        see doc : 
        Polar devices follow a predefined directory structure for measurement data. The
        path parts are as follows ”/U/X/YYYYMMDD/R/HHMMSS/XXX.REC”, where
        • U, The root folder for measurement
        data• X, User number
        • YYYYMMDD, Date of the measure-
        ment start date• R, date based folder containing record-
        ing data for this day
        • HHMMSS, local time at which the
        recording was started• XXX, name of the file, depending on
        which type is recorded
        • .REC, extension indicating that this
        file is Polar sensor device compatible
        offline recording file
        """
    def _compile_protobuf_request(self):
        """ compile protobuf file and encode as bytearray"""

    def send_request(self):
        """send comiled protobuf request as bytearray to pftp, 
        get response"""

    def decode_downloaded_file(self):
        """ parse file donwloaded from polar h10's pftp
            see doc: 
        """

