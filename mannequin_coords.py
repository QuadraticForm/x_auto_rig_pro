from mathutils import Vector, Euler, Matrix

coords={'pelvis': Vector((1.1648752433757181e-06, -0.03546452522277832, 9.705429077148438)), 'spine_01': Vector((2.2932558749744203e-06, 0.6045663356781006, 19.095504760742188)), 'spine_02': Vector((1.5992075077519985e-06, 1.5650908946990967, 13.322303771972656)), 'spine_03': Vector((1.661253463680623e-06, 2.3110668659210205, 13.840438842773438)), 'clavicle_l': Vector((13.918235778808594, 6.9506120681762695, -2.6709747314453125)), 'upperarm_l': Vector((9.943408966064453, 1.1179428100585938, -11.732620239257812)), 'lowerarm_l': Vector((14.720138549804688, -8.791529655456543, -11.214599609375)), 'hand_l': Vector((7.418285369873047, -4.771677017211914, -6.2159423828125)), 'index_01_l': Vector((1.6297721862792969, -1.3284335136413574, -3.7365493774414062)), 'index_02_l': Vector((0.764068603515625, -0.6675519943237305, -3.23858642578125)), 'index_03_l': Vector((1.1548080444335938, -1.0154056549072266, -3.0254287719726562)), 'middle_01_l': Vector((2.0407943725585938, -1.2454519271850586, -3.977081298828125)), 'middle_02_l': Vector((0.9041290283203125, -0.8172664642333984, -3.4392852783203125)), 'middle_03_l': Vector((1.8407974243164062, -0.799962043762207, -3.0472183227539062)), 'pinky_01_l': Vector((1.9121170043945312, -0.28551551699638367, -3.0023727416992188)), 'pinky_02_l': Vector((1.0753021240234375, -0.2280139923095703, -2.7759170532226562)), 'pinky_03_l': Vector((1.03009033203125, -0.43166860938072205, -2.76885986328125)), 'ring_01_l': Vector((2.0166549682617188, -0.8928370475769043, -3.8422012329101562)), 'ring_02_l': Vector((0.841827392578125, -0.5747072696685791, -3.3238754272460938)), 'ring_03_l': Vector((1.549285888671875, -0.7849781513214111, -3.011749267578125)), 'thumb_01_l': Vector((0.12947463989257812, -3.2002079486846924, -2.171722412109375)), 'thumb_02_l': Vector((0.1767120361328125, -2.4893083572387695, -3.2051925659179688)), 'thumb_03_l': Vector((-0.3583641052246094, -2.9913997650146484, -2.7247543334960938)), 'clavicle_r': Vector((-13.918163299560547, 6.9505720138549805, -2.67095947265625)), 'upperarm_r': Vector((-9.943452835083008, 1.1179475784301758, -11.732650756835938)), 'lowerarm_r': Vector((-14.720176696777344, -8.79155445098877, -11.214614868164062)), 'hand_r': Vector((-7.418270111083984, -4.771677017211914, -6.215934753417969)), 'index_01_r': Vector((-1.6298408508300781, -1.3284940719604492, -3.7367095947265625)), 'index_02_r': Vector((-0.764068603515625, -0.6675558090209961, -3.23858642578125)), 'index_03_r': Vector((-1.154815673828125, -1.0154085159301758, -3.0254364013671875)), 'middle_01_r': Vector((-2.0408782958984375, -1.2455048561096191, -3.9772415161132812)), 'middle_02_r': Vector((-0.9041519165039062, -0.8172807693481445, -3.4393463134765625)), 'middle_03_r': Vector((-1.840850830078125, -0.7999820709228516, -3.0472640991210938)), 'pinky_01_r': Vector((-1.9121551513671875, -0.2855238914489746, -3.00244140625)), 'pinky_02_r': Vector((-1.075225830078125, -0.22799871861934662, -2.7757110595703125)), 'pinky_03_r': Vector((-1.0300140380859375, -0.43163785338401794, -2.768646240234375)), 'ring_01_r': Vector((-2.016510009765625, -0.8927762508392334, -3.8419265747070312)), 'ring_02_r': Vector((-0.8418350219726562, -0.5747084617614746, -3.3238754272460938)), 'ring_03_r': Vector((-1.549346923828125, -0.7849829196929932, -3.0117340087890625)), 'thumb_01_r': Vector((-0.12947463989257812, -3.200113534927368, -2.1716537475585938)), 'thumb_02_r': Vector((-0.17670440673828125, -2.489307403564453, -3.2052078247070312)), 'thumb_03_r': Vector((0.3583488464355469, -2.9914073944091797, -2.7247467041015625)), 'neck_01': Vector((1.0827247933775652e-06, -2.252087116241455, 9.013656616210938)), 'head': Vector((1.1142928997287527e-06, 0.2140827178955078, 16.578201293945312)), 'thigh_l': Vector((3.9585037231445312, 0.9658896923065186, -32.07537841796875)), 'calf_l': Vector((2.157259941101074, 4.733462333679199, -29.887414932250977)), 'foot_l': Vector((0.8955478668212891, -19.57691764831543, -0.23760986328125)), 'thigh_r': Vector((-3.958521842956543, 0.9658963084220886, -32.075477600097656)), 'calf_r': Vector((-2.157278060913086, 4.7334885597229, -29.887554168701172)), 'foot_r': Vector((-0.8955459594726562, -19.576862335205078, -0.23760986328125))}         

matrix_coords = {'pelvis': Matrix(((-4.229695704793812e-08, 1.200222499164738e-07, 1.0, 1.3209631955987677e-13),
        (0.9999933242797852, -0.0036540713626891375, 4.2756944651500817e-08, 1.0561532974243164),
        (0.003654071595519781, 0.9999932646751404, -1.2607584665147442e-07, 96.75060272216797),
        (0.0, 0.0, 0.0, 1.0))), 'spine_01': Matrix(((-2.8462753220992454e-07, 1.2003386018477613e-07, 1.0, 1.1648753570625558e-06),
        (0.9994992017745972, 0.03164428099989891, 2.8070829216630955e-07, 1.0206879377365112),
        (-0.03164427727460861, 0.9994992017745972, -1.3518952357571834e-07, 106.45602416992188),
        (0.0, 0.0, 0.0, 1.0))), 'spine_02': Matrix(((-2.9596455419778067e-07, 1.1921997611352708e-07, 1.0, 3.4581310046633007e-06),
        (0.9931699633598328, 0.11667661368846893, 2.8005459284941026e-07, 1.6252543926239014),
        (-0.11667660623788834, 0.9931699633598328, -1.5914679352135863e-07, 125.5515365600586),
        (0.0, 0.0, 0.0, 1.0))), 'spine_03': Matrix(((-2.9905967835475167e-07, 1.1838982771905648e-07, 1.0, 5.057339421910001e-06),
        (0.986344039440155, 0.1646990031003952, 2.7549864967113535e-07, 3.190345525741577),
        (-0.1646990031003952, 0.986344039440155, -1.7223685233602737e-07, 138.87384033203125),
        (0.0, 0.0, 0.0, 1.0))), 'clavicle_l': Matrix(((-0.446773499250412, 0.8817449808120728, -0.1513913869857788, 3.7819902896881104),
        (0.8946472406387329, 0.44033363461494446, -0.07558446377515793, 2.7603952884674072),
        (1.6519312339369208e-05, -0.16921107470989227, -0.9855800271034241, 152.2012176513672),
        (0.0, 0.0, 0.0, 1.0))), 'upperarm_l': Matrix(((-0.06804922223091125, 0.6448396444320679, -0.7612826824188232, 17.700225830078125),
        (0.9969837069511414, 0.07249969244003296, -0.02770773135125637, 9.711007118225098),
        (0.03732571005821228, -0.7608718872070312, -0.6478280425071716, 149.53024291992188),
        (0.0, 0.0, 0.0, 1.0))), 'lowerarm_l': Matrix(((0.22621281445026398, 0.7184910774230957, -0.6577221751213074, 37.264617919921875),
        (0.8883807063102722, -0.4291152060031891, -0.1632186323404312, 11.910643577575684),
        (-0.39950963854789734, -0.5473853945732117, -0.7353649735450745, 126.4454345703125),
        (0.0, 0.0, 0.0, 1.0))), 'hand_l': Matrix(((-0.6143574714660645, 0.687474250793457, -0.38722604513168335, 56.64602279663086),
        (0.06881905347108841, -0.4422054886817932, -0.8942699432373047, 0.33520039916038513),
        (-0.7860209941864014, -0.5760498046875, 0.2243608981370926, 111.67963409423828),
        (0.0, 0.0, 0.0, 1.0))), 'index_01_l': Matrix(((-0.5691731572151184, 0.3801206946372986, 0.7290747761726379, 63.04233169555664),
        (-0.8210585713386536, -0.3098382353782654, -0.4794408679008484, -6.766398906707764),
        (0.04364985600113869, -0.871497631072998, 0.48845309019088745, 103.81494903564453),
        (0.0, 0.0, 0.0, 1.0))), 'index_02_l': Matrix(((-0.585664689540863, 0.2251366823911667, 0.7786595821380615, 64.6720962524414),
        (-0.8100419044494629, -0.1966976374387741, -0.5523969531059265, -8.094826698303223),
        (0.028795704245567322, -0.9542659521102905, 0.29756906628608704, 100.07840728759766),
        (0.0, 0.0, 0.0, 1.0))), 'index_03_l': Matrix(((-0.6060659885406494, 0.34027042984962463, 0.718957781791687, 65.43616485595703),
        (-0.7946281433105469, -0.29919469356536865, -0.5282506346702576, -8.76237678527832),
        (0.035360340029001236, -0.8914587497711182, 0.45172011852264404, 96.83982849121094),
        (0.0, 0.0, 0.0, 1.0))), 'middle_01_l': Matrix(((-0.3635391294956207, 0.4397900402545929, 0.8212334513664246, 64.49006652832031),
        (-0.9258252382278442, -0.268393874168396, -0.2661076486110687, -4.479488372802734),
        (0.10338252037763596, -0.8570587635040283, 0.5047404170036316, 103.48133850097656),
        (0.0, 0.0, 0.0, 1.0))), 'middle_02_l': Matrix(((-0.3366374969482422, 0.2477850615978241, 0.9084477424621582, 66.53084564208984),
        (-0.9321918487548828, -0.223979189991951, -0.28434428572654724, -5.724926948547363),
        (0.1330171823501587, -0.9425686597824097, 0.3063829839229584, 99.50428009033203),
        (0.0, 0.0, 0.0, 1.0))), 'middle_03_l': Matrix(((-0.3099198043346405, 0.5044887661933899, 0.8058791756629944, 67.43497467041016),
        (-0.9487491846084595, -0.2192372977733612, -0.22761887311935425, -6.542197227478027),
        (0.06184768304228783, -0.8351202011108398, 0.5465795397758484, 96.06497955322266),
        (0.0, 0.0, 0.0, 1.0))), 'pinky_01_l': Matrix(((0.04751281440258026, 0.5354589819908142, 0.8432237505912781, 64.02503204345703),
        (-0.9910808205604553, -0.07995401322841644, 0.1066162958741188, 0.1589190512895584),
        (0.1245078295469284, -0.840768039226532, 0.5268843173980713, 103.0174789428711),
        (0.0, 0.0, 0.0, 1.0))), 'pinky_02_l': Matrix(((0.03849969804286957, 0.3601592779159546, 0.9320958256721497, 65.9371337890625),
        (-0.9945775270462036, -0.07637037336826324, 0.07058988511562347, -0.12659138441085815),
        (0.0966082513332367, -0.92975914478302, 0.3552662432193756, 100.01512145996094),
        (0.0, 0.0, 0.0, 1.0))), 'pinky_03_l': Matrix(((0.007947970181703568, 0.3450157046318054, 0.9385631084442139, 67.01244354248047),
        (-0.9875791072845459, -0.14458177983760834, 0.061511438339948654, -0.3546048402786255),
        (0.15692172944545746, -0.9273938536643982, 0.3395812511444092, 97.23920440673828),
        (0.0, 0.0, 0.0, 1.0))), 'ring_01_l': Matrix(((-0.10225797444581985, 0.45520755648612976, 0.8844938278198242, 64.57563018798828),
        (-0.9794354438781738, -0.2015346735715866, -0.00951364915817976, -2.082643985748291),
        (0.1739254891872406, -0.8672772645950317, 0.4664549231529236, 103.03923034667969),
        (0.0, 0.0, 0.0, 1.0))), 'ring_02_l': Matrix(((-0.10031915456056595, 0.24213728308677673, 0.9650415778160095, 66.59227752685547),
        (-0.9843635559082031, -0.16530472040176392, -0.06085139140486717, -2.9754717350006104),
        (0.14479148387908936, -0.9560566544532776, 0.254934161901474, 99.19705200195312),
        (0.0, 0.0, 0.0, 1.0))), 'ring_03_l': Matrix(((-0.11813013255596161, 0.4456256926059723, 0.8873910307884216, 67.4341049194336),
        (-0.9740408658981323, -0.22578562796115875, -0.01628129743039608, -3.550182342529297),
        (0.19310471415519714, -0.8662786483764648, 0.4607296288013458, 95.8731689453125),
        (0.0, 0.0, 0.0, 1.0))), 'thumb_01_l': Matrix(((-0.8114516139030457, 0.03345847874879837, -0.5834610462188721, 57.478004455566406),
        (0.3053356409072876, -0.8269941806793213, -0.47207140922546387, -3.876652479171753),
        (-0.49831369519233704, -0.5612143278121948, 0.6608496308326721, 107.63906860351562),
        (0.0, 0.0, 0.0, 1.0))), 'thumb_02_l': Matrix(((-0.8151490688323975, 0.043502021580934525, -0.5776151418685913, 57.60746383666992),
        (0.43485209345817566, -0.6128039360046387, -0.6598294377326965, -7.076839923858643),
        (-0.38266855478286743, -0.7890368103981018, 0.4806097447872162, 105.46736145019531),
        (0.0, 0.0, 0.0, 1.0))), 'thumb_03_l': Matrix(((-0.7895573377609253, -0.08821988850831985, -0.6073031425476074, 57.784183502197266),
        (0.46224895119667053, -0.7364051342010498, -0.4939976930618286, -9.56616497039795),
        (-0.403641015291214, -0.6707644462585449, 0.6222134828567505, 102.26215362548828),
        (0.0, 0.0, 0.0, 1.0))), 'clavicle_r': Matrix(((-0.4467734396457672, -0.8817448019981384, 0.15139101445674896, -3.781996011734009),
        (-0.8946470618247986, 0.4403333365917206, -0.0755850076675415, 2.7603979110717773),
        (-1.583617449796293e-05, -0.16921088099479675, -0.9855799078941345, 152.20132446289062),
        (0.0, 0.0, 0.0, 1.0))), 'upperarm_r': Matrix(((-0.06804898381233215, -0.6448401808738708, 0.7612817883491516, -17.700159072875977),
        (-0.9969834089279175, 0.07249974459409714, -0.02770717814564705, 9.710969924926758),
        (-0.03732605651021004, -0.7608709931373596, -0.6478286981582642, 149.53036499023438),
        (0.0, 0.0, 0.0, 1.0))), 'lowerarm_r': Matrix(((0.2262129783630371, -0.7184911370277405, 0.6577216982841492, -37.26463317871094),
        (-0.8883801698684692, -0.4291154444217682, -0.16321878135204315, 11.910612106323242),
        (0.39950984716415405, -0.5473848581314087, -0.735365092754364, 126.44550323486328),
        (0.0, 0.0, 0.0, 1.0))), 'hand_r': Matrix(((-0.614357590675354, -0.6874740719795227, 0.38722577691078186, -56.6461067199707),
        (-0.06881833076477051, -0.44220587611198425, -0.8942694664001465, 0.335093230009079),
        (0.7860208749771118, -0.5760496258735657, 0.22436173260211945, 111.6796646118164),
        (0.0, 0.0, 0.0, 1.0))), 'index_01_r': Matrix(((-0.5691726207733154, -0.38012033700942993, -0.7290751338005066, -63.0421257019043),
        (0.8210582733154297, -0.3098389208316803, -0.47944003343582153, -6.766444206237793),
        (-0.043650854378938675, -0.8714977502822876, 0.4884530007839203, 103.81487274169922),
        (0.0, 0.0, 0.0, 1.0))), 'index_02_r': Matrix(((-0.5856645703315735, -0.2251366823911667, -0.7786595225334167, -64.67206573486328),
        (0.8100418448448181, -0.1966983824968338, -0.5523967146873474, -8.094910621643066),
        (-0.028796259313821793, -0.9542659521102905, 0.2975693941116333, 100.07819366455078),
        (0.0, 0.0, 0.0, 1.0))), 'index_03_r': Matrix(((-0.6060663461685181, -0.3402716815471649, -0.7189565300941467, -65.43624877929688),
        (0.7946275472640991, -0.2991943657398224, -0.5282513499259949, -8.762526512145996),
        (-0.03535887226462364, -0.89145827293396, 0.4517209827899933, 96.83966064453125),
        (0.0, 0.0, 0.0, 1.0))), 'middle_01_r': Matrix(((-0.36353906989097595, -0.4397902488708496, -0.8212329745292664, -64.4899673461914),
        (0.9258246421813965, -0.2683942914009094, -0.2661074697971344, -4.479549407958984),
        (-0.10338275879621506, -0.8570584058761597, 0.5047407150268555, 103.48140716552734),
        (0.0, 0.0, 0.0, 1.0))), 'middle_02_r': Matrix(((-0.3366391062736511, -0.2477870136499405, -0.9084470272064209, -66.53070831298828),
        (0.9321915507316589, -0.22397920489311218, -0.2843455374240875, -5.725009918212891),
        (-0.13301631808280945, -0.9425680041313171, 0.3063851594924927, 99.50408935546875),
        (0.0, 0.0, 0.0, 1.0))), 'middle_03_r': Matrix(((-0.3099253475666046, -0.5044938325881958, -0.8058739304542542, -67.43489074707031),
        (0.9487475156784058, -0.21923863887786865, -0.22762414813041687, -6.542298793792725),
        (-0.06184371933341026, -0.835116982460022, 0.5465850234031677, 96.06475067138672),
        (0.0, 0.0, 0.0, 1.0))), 'pinky_01_r': Matrix(((0.04751451313495636, -0.5354576706886292, -0.843224287033081, -64.0249252319336),
        (0.9910799264907837, -0.07995463162660599, 0.10661827027797699, 0.15880289673805237),
        (-0.12450923770666122, -0.8407688736915588, 0.5268825888633728, 103.01740264892578),
        (0.0, 0.0, 0.0, 1.0))), 'pinky_02_r': Matrix(((0.03849925845861435, -0.36016035079956055, -0.9320957660675049, -65.93700408935547),
        (0.9945777654647827, -0.07637091726064682, 0.07058952748775482, -0.12671200931072235),
        (-0.09660845249891281, -0.9297592639923096, 0.3552672564983368, 100.0149154663086),
        (0.0, 0.0, 0.0, 1.0))), 'pinky_03_r': Matrix(((0.007947699166834354, -0.34501636028289795, -0.9385628700256348, -67.01251983642578),
        (0.9875790476799011, -0.1445825845003128, 0.06151128560304642, -0.3546583354473114),
        (-0.15692216157913208, -0.9273939728736877, 0.3395817279815674, 97.23929595947266),
        (0.0, 0.0, 0.0, 1.0))), 'ring_01_r': Matrix(((-0.10225772857666016, -0.455207496881485, -0.8844936490058899, -64.57562255859375),
        (0.9794350266456604, -0.20153526961803436, -0.009513202123343945, -2.082777738571167),
        (-0.1739262342453003, -0.8672771453857422, 0.46645480394363403, 103.03902435302734),
        (0.0, 0.0, 0.0, 1.0))), 'ring_02_r': Matrix(((-0.1003212109208107, -0.24213962256908417, -0.965040922164917, -66.59220886230469),
        (0.9843636155128479, -0.16530494391918182, -0.060853008180856705, -2.9755239486694336),
        (-0.1447911560535431, -0.9560561776161194, 0.2549368739128113, 99.19713592529297),
        (0.0, 0.0, 0.0, 1.0))), 'ring_03_r': Matrix(((-0.11814947426319122, -0.4456413686275482, -0.8873807787895203, -67.4340591430664),
        (0.9740407466888428, -0.22578594088554382, -0.01629839837551117, -3.5502378940582275),
        (-0.19309480488300323, -0.8662706017494202, 0.4607492983341217, 95.87325286865234),
        (0.0, 0.0, 0.0, 1.0))), 'thumb_01_r': Matrix(((-0.8114496469497681, -0.03345969691872597, 0.5834633708000183, -57.47806930541992),
        (-0.3053355813026428, -0.8269946575164795, -0.47206979990005493, -3.876774549484253),
        (0.4983166754245758, -0.5612133145332336, 0.6608481407165527, 107.63893127441406),
        (0.0, 0.0, 0.0, 1.0))), 'thumb_02_r': Matrix(((-0.8151518106460571, -0.04350009188055992, 0.5776116847991943, -57.607421875),
        (-0.43485110998153687, -0.6128020286560059, -0.6598318219184875, -7.076915740966797),
        (0.38266435265541077, -0.7890383005142212, 0.48061060905456543, 105.46731567382812),
        (0.0, 0.0, 0.0, 1.0))), 'thumb_03_r': Matrix(((-0.7895520329475403, 0.08821629732847214, 0.6073099970817566, -57.78410720825195),
        (-0.4622499346733093, -0.7364071011543274, -0.49399346113204956, -9.566225051879883),
        (0.4036492705345154, -0.6707625389099121, 0.6222096085548401, 102.26209259033203),
        (0.0, 0.0, 0.0, 1.0))), 'neck_01': Matrix(((-2.3212557209717488e-08, 1.1653806097911001e-07, 1.0, 7.162889687606366e-06),
        (0.9701763987541199, -0.24240119755268097, 5.0790831096492184e-08, 5.874691486358643),
        (0.24240122735500336, 0.9701762795448303, -1.1364462437768452e-07, 156.4210205078125),
        (0.0, 0.0, 0.0, 1.0))), 'head': Matrix(((-9.636880804464454e-08, 6.72087594466575e-08, 1.0, 8.255305147031322e-06),
        (0.9999169111251831, 0.01291242241859436, 9.551456514600432e-08, 3.9776296615600586),
        (-0.012912333011627197, 0.9999167323112488, -7.465644102921942e-08, 165.51602172851562),
        (0.0, 0.0, 0.0, 1.0))), 'thigh_l': Matrix(((-0.1477910429239273, 0.12242862582206726, -0.9814277291297913, 9.005809783935547),
        (0.9889518618583679, 0.029873045161366463, -0.14519551396369934, 0.5300276279449463),
        (0.01154157891869545, -0.9920275807380676, -0.12549078464508057, 95.29984283447266),
        (0.0, 0.0, 0.0, 1.0))), 'calf_l': Matrix(((-0.0635368600487709, 0.07111050188541412, -0.9954585433006287, 14.217846870422363),
        (0.9863924980163574, 0.15603072941303253, -0.0518101267516613, 1.8017840385437012),
        (0.1516353040933609, -0.9851890206336975, -0.08005710691213608, 53.067203521728516),
        (0.0, 0.0, 0.0, 1.0))), 'foot_l': Matrix(((-0.014876925386488438, 0.04569392651319504, 0.9988604784011841, 17.076255798339844),
        (-0.012815532274544239, -0.9988817572593689, 0.045502036809921265, 8.073701858520508),
        (0.9998070597648621, -0.01212367508560419, 0.015447469428181648, 13.465873718261719),
        (0.0, 0.0, 0.0, 1.0))), 'thigh_r': Matrix(((-0.14777860045433044, -0.1224287822842598, 0.9813987612724304, -9.005803108215332),
        (-0.9889523386955261, 0.02987314760684967, -0.14519134163856506, 0.5300224423408508),
        (-0.011543194763362408, -0.992027223110199, -0.12548740208148956, 95.3000259399414),
        (0.0, 0.0, 0.0, 1.0))), 'calf_r': Matrix(((-0.06352739781141281, -0.07111074030399323, 0.995428740978241, -14.217872619628906),
        (-0.9863924980163574, 0.1560308188199997, -0.05180623009800911, 1.8017913103103638),
        (-0.15163640677928925, -0.9851886630058289, -0.08005113899707794, 53.06718826293945),
        (0.0, 0.0, 0.0, 1.0))), 'foot_r': Matrix(((-0.01483417209237814, -0.04569394513964653, -0.9988307952880859, -17.076290130615234),
        (0.01281293947249651, -0.9988816380500793, 0.04550791531801224, 8.073735237121582),
        (-0.9998072385787964, -0.01212369091808796, 0.015397943556308746, 13.465716361999512),
        (0.0, 0.0, 0.0, 1.0)))}